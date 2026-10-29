# Fábrica de livros de colorir: comando único usado pelos agentes da STARNET.
#
# Uso (sempre de dentro da pasta do motor):
#   fabrica status                      a placa está livre?
#   fabrica teste                       desenha 1 página de teste e mede o tempo
#   fabrica desenhar <roteiro.json>     desenha as variações de cada página
#   fabrica acabar   <roteiro.json>     acabamento de todas as variações
#   fabrica conferir <roteiro.json>     conferência automática + melhor de cada página
#   fabrica livro    <roteiro.json>     desenhar + acabar + conferir
# No lugar de <roteiro.json> pode ir só o código do livro (ex.: dino-01), que é
# procurado na pasta "livros" do config.json.
#   fabrica montar   <roteiro.json>     PDF do miolo com as escolhas do revisor
# Opções: --paginas 1,2,5   --variacoes 4   --nao-esperar
#
# Cada etapa escreve no stdout linhas JSON ({"progresso": ...}, {"aviso": ...},
# {"fim": ...}), como os scripts do estúdio de dublagem.
import argparse
import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import acabamento  # noqa: E402
import conferir as conf  # noqa: E402
import placa  # noqa: E402

FORMATOS = {'A4': (210, 297), 'carta': (215.9, 279.4), 'A5': (148, 210)}


def emitir(obj):
    print(json.dumps(obj, ensure_ascii=False), flush=True)


def ler_config():
    caminho = os.path.join(AQUI, 'config.json')
    if os.path.exists(caminho):
        with open(caminho, encoding='utf-8') as f:
            return json.load(f)
    return {}


def achar_roteiro(nome):
    """Aceita o caminho do roteiro.json ou só o código do livro, procurado na
    pasta de livros do config.json (assim o agente não precisa de caminho)."""
    if os.path.isfile(nome):
        return nome
    pasta = ler_config().get('livros')
    if pasta:
        caminho = os.path.join(pasta, nome, 'roteiro.json')
        if os.path.isfile(caminho):
            return caminho
    emitir({'erro': f'roteiro não encontrado: {nome}'})
    sys.exit(2)


def ler_roteiro(caminho):
    caminho = achar_roteiro(caminho)
    with open(caminho, encoding='utf-8') as f:
        roteiro = json.load(f)
    roteiro['_pasta'] = os.path.dirname(os.path.abspath(caminho))
    idade = roteiro.get('idade', '5-8')
    regra = conf.regra_da_idade(idade)
    estilo = roteiro.setdefault('estilo', {})
    estilo.setdefault('traco_mm', regra['traco_mm'])
    pagina = roteiro.setdefault('pagina', {})
    largura, altura = FORMATOS.get(pagina.get('formato', 'A4'), FORMATOS['A4'])
    pagina.setdefault('largura_mm', largura)
    pagina.setdefault('altura_mm', altura)
    pagina.setdefault('margem_mm', 12)
    return roteiro


def pasta_da_pagina(roteiro, n):
    pasta = os.path.join(roteiro['_pasta'], 'paginas', f'{int(n):02d}')
    os.makedirs(pasta, exist_ok=True)
    return pasta


def escolher_paginas(roteiro, filtro):
    paginas = roteiro.get('paginas', [])
    if filtro:
        quero = {int(x) for x in filtro.split(',') if x.strip()}
        paginas = [p for p in paginas if int(p['n']) in quero]
    return paginas


def esperar_placa(nao_esperar):
    while True:
        s = placa.situacao()
        if s['livre'] or s['motivo'] == 'placa NVIDIA não encontrada':
            return s
        if nao_esperar:
            emitir({'erro': f"placa ocupada: {s['motivo']}"})
            sys.exit(3)
        emitir({'aviso': f"aguardando a placa: {s['motivo']}"})
        time.sleep(60)


def cmd_status(_args):
    emitir(placa.situacao())


def cmd_desenhar(args, roteiro=None):
    roteiro = roteiro or ler_roteiro(args.roteiro)
    from desenhar import Desenhista

    paginas = escolher_paginas(roteiro, args.paginas)
    variacoes = int(args.variacoes or roteiro.get('variacoes', 6))
    semente = int(roteiro.get('semente', 1000))
    personagens = roteiro.get('personagens', {})
    usa_personagem = any(p.get('personagem') for p in paginas)
    esperar_placa(args.nao_esperar)
    emitir({'etapa': 'carregando o modelo'})
    desenhista = Desenhista(ler_config().get('desenho'), com_personagem=usa_personagem)
    total = len(paginas) * variacoes
    feitas = 0
    for p in paginas:
        pasta = pasta_da_pagina(roteiro, p['n'])
        ficha = personagens.get(p.get('personagem') or '', {})
        referencia = ficha.get('referencia')
        if referencia:
            referencia = os.path.join(roteiro['_pasta'], referencia)
        for v in range(1, variacoes + 1):
            destino = os.path.join(pasta, f'v{v}.png')
            if os.path.exists(destino):
                feitas += 1
                continue
            esperar_placa(args.nao_esperar)
            imagem, segundos = desenhista.desenhar(
                p['prompt'], semente + int(p['n']) * 100 + v,
                negativo_extra=p.get('negativo', ''), referencia=referencia,
                forca=float(ficha.get('forca', 0.6)))
            imagem.save(destino)
            feitas += 1
            emitir({'progresso': round(feitas / total, 3), 'pagina': p['n'], 'variacao': v,
                    'segundos': round(segundos, 1)})
    emitir({'fim': 'desenhar', 'imagens': feitas})


def variacoes_da_pasta(pasta):
    return sorted(f for f in os.listdir(pasta) if f.startswith('v') and f.endswith('.png') and '-' not in f)


def cmd_acabar(args, roteiro=None):
    roteiro = roteiro or ler_roteiro(args.roteiro)
    pag, est = roteiro['pagina'], roteiro['estilo']
    feitas = 0
    for p in escolher_paginas(roteiro, args.paginas):
        pasta = pasta_da_pagina(roteiro, p['n'])
        for arquivo in variacoes_da_pasta(pasta):
            nome = arquivo[:-4]
            medidas = acabamento.acabar(
                os.path.join(pasta, arquivo), os.path.join(pasta, f'{nome}-final.png'),
                largura_mm=pag['largura_mm'], altura_mm=pag['altura_mm'], margem_mm=pag['margem_mm'],
                traco_mm=est['traco_mm'], esvaziar=est.get('esvaziar_manchas', True))
            with open(os.path.join(pasta, f'{nome}-medidas.json'), 'w', encoding='utf-8') as f:
                json.dump(medidas, f, ensure_ascii=False, indent=2)
            feitas += 1
            emitir({'acabada': f"{int(p['n']):02d}/{arquivo}"})
    emitir({'fim': 'acabar', 'imagens': feitas})


def cmd_conferir(args, roteiro=None):
    roteiro = roteiro or ler_roteiro(args.roteiro)
    idade = roteiro.get('idade', '5-8')
    relatorio = {'codigo': roteiro.get('codigo'), 'idade': idade, 'paginas': []}
    for p in escolher_paginas(roteiro, args.paginas):
        pasta = pasta_da_pagina(roteiro, p['n'])
        resultados = []
        for arquivo in variacoes_da_pasta(pasta):
            nome = arquivo[:-4]
            final = os.path.join(pasta, f'{nome}-final.png')
            if not os.path.exists(final):
                continue
            caminho_medidas = os.path.join(pasta, f'{nome}-medidas.json')
            medidas = None
            if os.path.exists(caminho_medidas):
                with open(caminho_medidas, encoding='utf-8') as f:
                    medidas = json.load(f)
            r = conf.conferir(os.path.join(pasta, arquivo), final, idade, medidas)
            r['variacao'] = nome
            resultados.append(r)
        resultados.sort(key=lambda r: (not r['passou'], -r['nota']))
        melhor = resultados[0]['variacao'] if resultados and resultados[0]['passou'] else None
        relatorio['paginas'].append({'n': p['n'], 'cena': p.get('cena', ''), 'sugestao': melhor,
                                     'variacoes': resultados})
        emitir({'conferida': p['n'], 'sugestao': melhor})
    destino = os.path.join(roteiro['_pasta'], 'conferencia-automatica.json')
    with open(destino, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
    sem = [pg['n'] for pg in relatorio['paginas'] if not pg['sugestao']]
    emitir({'fim': 'conferir', 'arquivo': 'conferencia-automatica.json', 'paginas_sem_aprovada': sem})


def cmd_livro(args):
    roteiro = ler_roteiro(args.roteiro)
    cmd_desenhar(args, roteiro)
    cmd_acabar(args, roteiro)
    cmd_conferir(args, roteiro)


def cmd_montar(args):
    from montar import montar

    roteiro = ler_roteiro(args.roteiro)
    caminho = os.path.join(roteiro['_pasta'], 'escolhas.json')
    if not os.path.exists(caminho):
        emitir({'erro': 'falta escolhas.json (o revisor grava {"1": "v3", "2": "v1", ...})'})
        sys.exit(2)
    with open(caminho, encoding='utf-8') as f:
        escolhas = json.load(f)
    arquivos, faltam = [], []
    for p in roteiro['paginas']:
        nome = escolhas.get(str(p['n']))
        arquivo = nome and os.path.join(pasta_da_pagina(roteiro, p['n']), f'{nome}-final.png')
        if arquivo and os.path.exists(arquivo):
            arquivos.append(arquivo)
        else:
            faltam.append(p['n'])
    if faltam:
        emitir({'erro': f'páginas sem escolha aprovada: {faltam}'})
        sys.exit(2)
    pasta_final = os.path.join(roteiro['_pasta'], 'final')
    os.makedirs(pasta_final, exist_ok=True)
    pag = roteiro['pagina']
    extras = roteiro.get('extras', {})
    total = montar(
        arquivos, os.path.join(pasta_final, 'miolo.pdf'),
        largura_mm=pag['largura_mm'], altura_mm=pag['altura_mm'],
        titulo=roteiro.get('titulo', ''), autor=roteiro.get('autor', ''),
        idioma=roteiro.get('idioma', 'pt'), verso_branco=roteiro.get('verso_branco', True),
        pertence_imagem=extras.get('pertence') and os.path.join(roteiro['_pasta'], extras['pertence']),
        final=extras.get('final') and os.path.join(roteiro['_pasta'], extras['final']))
    emitir({'fim': 'montar', 'arquivo': 'final/miolo.pdf', 'paginas_pdf': total})


def cmd_teste(args):
    roteiro = os.path.join(AQUI, 'exemplos', 'teste', 'roteiro.json')
    args.roteiro = roteiro
    args.paginas = '1'
    args.variacoes = 1
    inicio = time.time()
    cmd_livro(args)
    emitir({'fim': 'teste', 'segundos_total': round(time.time() - inicio, 1),
            'pasta': os.path.join('exemplos', 'teste', 'paginas', '01')})


def main():
    p = argparse.ArgumentParser(description='Fábrica de livros de colorir')
    p.add_argument('comando', choices=['status', 'teste', 'desenhar', 'acabar', 'conferir', 'livro', 'montar'])
    p.add_argument('roteiro', nargs='?')
    p.add_argument('--paginas')
    p.add_argument('--variacoes')
    p.add_argument('--nao-esperar', action='store_true')
    args = p.parse_args()
    if args.comando not in ('status', 'teste') and not args.roteiro:
        p.error('informe o roteiro.json')
    globals()['cmd_' + args.comando](args)


if __name__ == '__main__':
    main()
