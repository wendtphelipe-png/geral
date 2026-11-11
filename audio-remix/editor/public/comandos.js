// Entende pedidos escritos em português sobre os oitos selecionados.
// Gratuito e local: funciona por regras. Devolve as ações e uma frase do que foi entendido.
(function (raiz) {
  const FAIXAS = ["voz", "bateria", "baixo", "outros"];
  const NOME = {voz: "voz", bateria: "bateria", baixo: "baixo", outros: "outros instrumentos"};

  const semAcento = t => t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

  function faixasCitadas(t) {
    const f = new Set();
    if (/\b(voz|vozes|vocal|vocais|cantor|cantora|artista|letra|canto)\b/.test(t)) f.add("voz");
    if (/\b(bateria|batida|batidas|drums?|percuss\w*|bumbo|caixa|chimbal)\b/.test(t)) f.add("bateria");
    // "baixo" como faixa (e não "mais baixo", "volume baixo")
    const semVolume = t.replace(/\b(mais|bem|volume|bem mais|um pouco mais)\s+baix[oa]\b/g, " ");
    if (/\b(baixo|graves?|bass|sub)\b/.test(semVolume)) f.add("baixo");
    if (/\b(outros|melodia|teclado|teclados|synth|sintetizador|guitarra|piano|cordas|metais)\b/.test(t)) f.add("outros");
    if (/\binstrumentos?\b|\binstrumental\b|\bbase\b/.test(t)) ["bateria", "baixo", "outros"].forEach(x => f.add(x));
    if (/\b(tudo|todas as faixas|todos)\b/.test(t)) FAIXAS.forEach(x => f.add(x));
    return [...f];
  }

  function porcentagem(t) {
    const m = t.match(/(\d{1,3})\s*%/);
    return m ? +m[1] / 100 : null;
  }

  const VERBO = "(tir|deix|coloc|aument|abaix|diminu|sem |so |somente|apenas|mais |menos|repet|duplic|apag|remov|volt|lig|deslig|silenc|mut|meio|tempo|sobe|reforc|traz|bot|corta|faz|quero|põe|poe)";
  const DIVISOR = new RegExp(`\\s*(?:,|;|\\.|\\be\\b(?=\\s+(?:a |o |os |as )?${VERBO})|\\bdepois\\b|\\btambem\\b)\\s*`);

  // Junta o entendimento de cada parte do pedido ("tira a voz e deixa o grave mais alto" = 2 partes)
  // Efeitos citados num trecho do pedido: eco, reverb, distante, abafado, rádio.
  function efeitosCitados(t) {
    const fx = {};
    const forca = /\b(muito|bastante|forte|pesad\w*|cheio)\b/.test(t) ? 0.75 : /\b(pouco|leve|sutil|suave|discreto)\b/.test(t) ? 0.3 : 0.5;
    if (/\b(eco|ecos|delay)\b/.test(t)) fx.eco = forca;
    if (/\b(reverb\w*|reverbera\w*|salao|catedral|igreja|ambiencia)\b/.test(t)) fx.reverb = forca;
    if (/\b(distante|longe|ao fundo|la no fundo|lembranca|memoria)\b/.test(t)) Object.assign(fx, {eco: fx.eco || 0.4, reverb: fx.reverb || 0.5, filtro: "abafado", distante: true});
    if (/\b(abafad\w*|outra sala|debaixo d.?agua|filtrad\w*)\b/.test(t)) fx.filtro = "abafado";
    if (/\b(radio|telefone|megafone|walkie)\b/.test(t)) fx.filtro = "radio";
    if (/\b(meio tempo de eco|eco curto)\b/.test(t)) fx.batidas_eco = 0.5;
    return fx;
  }
  const NOMES_FX = fx => [fx.distante ? "distante" : null, fx.eco && !fx.distante ? "eco" : null, fx.reverb && !fx.distante ? "reverb" : null,
    fx.filtro === "abafado" && !fx.distante ? "abafado" : null, fx.filtro === "radio" ? "rádio" : null].filter(Boolean).join(" + ");

  function entender(texto) {
    const t = semAcento(texto).replace(/\s+/g, " ").trim();
    if (!t) return {acoes: [], frases: [], faltando: [], vazio: true};

    // "coloca a voz do oito 5 aqui como eco distante, 30% mais baixa"
    const tr = t.match(/\b(voz|vocal|bateria|batida|baixo|grave|outros|instrumentos?|musica inteira|tudo)\b[^.;]{0,40}?\b(?:d[oa]|n[oa]|que (?:ele |ela )?usa no) (?:oito|trecho|bloco|parte) (\d+)\b/);
    const trazer = tr && /\b(coloc\w*|adicion\w*|traz\w*|trag\w*|bot\w*|poe|ponha|usa|use|insir\w*|insere|copi\w*|lev\w*|repet\w*)\b/.test(t)
      && !/\b(tir\w*|remov\w*|sem|apag\w*)\b/.test(t.slice(0, tr.index));
    if (trazer) {
      const faixa = {voz: "voz", vocal: "voz", bateria: "bateria", batida: "bateria", baixo: "baixo", grave: "baixo", outros: "outros"}[tr[1]] || "tudo";
      const pct = porcentagem(t);
      let ganho = 1;
      if (/mais baix[ao]|abaix|menos|mais fraco|mais suave/.test(t)) ganho = pct !== null ? Math.max(0, 1 - pct) : 0.6;
      else if (/mais alt[ao]|aument|mais forte/.test(t)) ganho = pct !== null ? 1 + pct : 1.4;
      const fx = efeitosCitados(t);
      const frase = `trazer ${faixa === "tudo" ? "o som inteiro" : NOME[faixa]} do oito ${tr[2]} da música original para uma camada` +
        (Object.keys(fx).length ? `, com ${NOMES_FX(fx)}` : "") + (ganho !== 1 ? `, volume ${Math.round(ganho * 100)}%` : "");
      return {acoes: [{tipo: "trazer", faixa, oito: tr[2], fx, ganho}], frases: [frase], faltando: [], vazio: false};
    }
    const partes = t.split(DIVISOR).map(x => x && x.trim()).filter(Boolean);
    const total = {acoes: [], frases: [], faltando: [], vazio: false};
    for (const parte of partes) {
      const r = entenderParte(parte);
      total.acoes.push(...r.acoes); total.frases.push(...r.frases);
      for (const f of r.faltando) if (!total.faltando.includes(f)) total.faltando.push(f);
    }
    return total;
  }

  function entenderParte(t) {
    const acoes = [], frases = [], faltando = [];

    // Pedidos que ainda não existem no editor (ficam registrados para as próximas etapas)
    const futuros = [
      [/\b(tom|afina|pitch|mais aguda|mais grave a voz)\b/, "mudar o tom"],
      [/\b(daquele trecho|de outro trecho|que ele usa)\b/, "trazer uma faixa de outro trecho sem dizer qual (diga \"a voz do oito 5\")"],
      [/\b(house|breaking|locking|popping|krump|waacking|vogue|passinho|funk|dancehall|amapiano|trap|boom ?bap)\b/, "injetar estilo"],
    ];
    for (const [re, nome] of futuros) if (re.test(t)) faltando.push(nome);
    // Uma parte que depende de algo que ainda não existe não mexe em nada (evita fazer pela metade)
    if (faltando.length) return {acoes, frases, faltando};

    const citadas = faixasCitadas(t);
    const pct = porcentagem(t);

    const citadasAqui = faixasCitadas(t);

    // tirar efeitos / paradas
    if (/\b(tir\w*|sem|remov\w*|limp\w*|desliga\w*)\b.*\b(efeitos?|eco|reverb|filtro|abafado|radio)\b/.test(t)) {
      acoes.push({tipo: "semFx", alvo: citadasAqui.length ? citadasAqui : null}); frases.push("tirar os efeitos" + (citadasAqui.length ? " de " + citadasAqui.map(f => NOME[f]).join(" e ") : ""));
      return {acoes, frases, faltando};
    }
    if (/\b(tir\w*|sem|remov\w*|limp\w*)\b.*\b(paradas?|stops?|hits?|freezes?)\b/.test(t)) {
      acoes.push({tipo: "semParadas"}); frases.push("tirar as paradas");
      return {acoes, frases, faltando};
    }

    // paradas: "parada no 5 e no 7", "stop no tempo 8", "freeze no 1 de 2 tempos"
    if (/\b(parad\w*|stops?|hits?|freez\w*|pausa\w*|corte seco|silencio)\b/.test(t)) {
      const semDuracao = t.replace(/\d+(?:[.,]\d+)?\s*(tempos?|batidas?|segundos?)/g, " ").replace(/\d{1,3}\s*%/g, " ");
      const tempos = [...new Set((semDuracao.match(/\b[1-8]\b/g) || []).map(Number))].sort((a, b) => a - b);
      const q = t.match(/(\d+(?:[.,]\d+)?)\s*(tempos?|batidas?)/);
      const dur = q ? parseFloat(q[1].replace(",", ".")) : /meio tempo|meia batida|rapid/.test(t) ? 0.5 : /freez|pausa/.test(t) ? 1 : 0.5;
      const lista = tempos.length ? tempos : [8];
      acoes.push({tipo: "paradas", tempos: lista, dur});
      frases.push(`parada${lista.length > 1 ? "s" : ""} no${lista.length > 1 ? "s tempos" : " tempo"} ${lista.join(", ")} (${dur === 0.5 ? "meio tempo" : dur + (dur === 1 ? " tempo" : " tempos")})`);
      return {acoes, frases, faltando};
    }

    // efeitos: "eco na voz", "reverb", "som de rádio", "deixa distante"
    const fxAqui = efeitosCitados(t);
    if (Object.keys(fxAqui).length) {
      const alvo = citadasAqui.length && citadasAqui.length < 4 ? citadasAqui : ["tudo"];
      acoes.push({tipo: "fx", alvo, fx: fxAqui});
      frases.push(`${NOMES_FX(fxAqui)} ${alvo[0] === "tudo" ? "no trecho inteiro" : "em " + alvo.map(f => NOME[f]).join(" e ")}`);
      // "distante" também abaixa um pouco o volume, se nada for dito sobre volume
      if (fxAqui.distante && !/%|mais alt|mais baix/.test(t)) {
        acoes.push({tipo: "faixas", mudancas: Object.fromEntries((alvo[0] === "tudo" ? FAIXAS : alvo).map(f => [f, {mult: 0.8}]))});
      }
      if (!/%|mais alt|mais baix|aument|diminu|abaix/.test(t)) return {acoes, frases, faltando};
    }

    // fades: "fade out de 2 oitos", "fade in 3 segundos", "entra suave", "some aos poucos"
    const fadeIn = /\bfade ?in\b|\bentra\w* (suave|aos poucos|devagar)|\bsurg\w* aos poucos|\baparec\w* aos poucos/.test(t);
    const fadeOut = /\bfade ?out\b|\bsai\w* (suave|aos poucos|devagar)|\bsome\w* aos poucos|\bvai sumindo|\bdesaparec\w*|\bterminar? suave/.test(t);
    if (fadeIn || fadeOut) {
      const q = t.match(/(\d+(?:[.,]\d+)?)\s*(segundos?|s\b|tempos?|batidas?|oitos?)/);
      let medida = null;
      if (q) {
        const v = parseFloat(q[1].replace(",", "."));
        medida = /seg|^s$/.test(q[2]) ? {seg: v} : /oito/.test(q[2]) ? {tempos: v * 8} : {tempos: v};
      }
      const dir = fadeIn ? "in" : "out";
      acoes.push(Object.assign({tipo: "fade", dir}, medida || {}));
      frases.push((dir === "in" ? "fade de entrada" : "fade de saída") + (medida ? (medida.seg ? ` de ${medida.seg} s` : ` de ${medida.tempos} tempos`) : " em toda a seleção"));
      return {acoes, frases, faltando};
    }

    // dividir: "corta ao meio", "divide em 4"
    const div = t.match(/\b(cort\w*|divid\w*|part\w*|quebr\w*)\b.*\b(no meio|ao meio|pela metade|em (dois|2|duas|quatro|4|oito|8))\b/);
    if (div) {
      const n = /quatro|4/.test(div[2]) ? 4 : /oito|8/.test(div[2]) ? 8 : 2;
      acoes.push({tipo: "dividir", partes: n}); frases.push(`dividir em ${n} partes`);
      return {acoes, frases, faltando};
    }

    // velocidade
    if (/meio tempo|half ?time|metade da velocidade|mais devagar|camera lenta/.test(t)) {
      acoes.push({tipo: "vel", valor: 0.5}); frases.push("meio tempo");
    } else if (/tempo dobrado|dobr\w* o tempo|double ?time|duas vezes mais rapido|acelera/.test(t)) {
      acoes.push({tipo: "vel", valor: 2}); frases.push("tempo dobrado");
    } else if (/(velocidade|tempo) normal/.test(t)) {
      acoes.push({tipo: "vel", valor: 1}); frases.push("velocidade normal");
    }

    // voltar ao original
    if (/\b(volta\w* ao (normal|original)|como era|desfaz tudo|original de novo|restaura)\b/.test(t)) {
      acoes.push({tipo: "faixas", mudancas: Object.fromEntries(FAIXAS.map(f => [f, {set: 1}]))});
      acoes.push({tipo: "vel", valor: 1});
      acoes.push({tipo: "semFade"}); acoes.push({tipo: "semFx", alvo: null}); acoes.push({tipo: "semParadas"});
      frases.push("tudo como na música original");
    }

    // só / apenas
    const so = t.match(/\b(so|somente|apenas|deixa\w* so|deixe apenas|deixa apenas|isola\w*)\b/);
    const soQuais = so ? faixasCitadas(t.slice(so.index)) : [];
    if (so && soQuais.length) {
      const m = {};
      for (const f of FAIXAS) m[f] = {set: soQuais.includes(f) ? 1 : 0};
      acoes.push({tipo: "faixas", mudancas: m});
      frases.push("só " + soQuais.map(f => NOME[f]).join(" e "));
    } else if (citadas.length) {
      const tirar = /\b(tir\w*|remov\w*|sem|silenci\w*|mut\w*|deslig\w*|cort\w*|apag\w*|exclu\w*|some|sumir|zera\w*)\b/.test(t);
      const voltar = /\b(volt\w*|coloc\w*|lig\w*|traz\w*|bot\w*|devolv\w*|com)\b/.test(t);
      const sobe = /\b(mais alt\w*|aumenta\w*|sob\w*|reforc\w*|mais forte|mais pesad\w*|turbina\w*|destaca\w*)\b/.test(t)
        || /\bmais (graves?|batidas?|bateria|voz|baixo)\b/.test(t);
      const desce = /\b(mais baix[ao]|abaix\w*|diminu\w*|menos|mais fraco|mais suave|mais leve|reduz\w*)\b/.test(t);
      const definir = t.match(/\b(em|a|para|no|com volume de)\s*(\d{1,3})\s*%/);
      const m = {};
      if (tirar && !sobe) {
        citadas.forEach(f => m[f] = {set: 0});
        frases.push("tirar " + citadas.map(f => NOME[f]).join(" e "));
      } else if (definir && !sobe && !desce) {
        citadas.forEach(f => m[f] = {set: +definir[2] / 100});
        frases.push(citadas.map(f => NOME[f]).join(" e ") + " em " + definir[2] + "%");
      } else if (desce) {
        // "voz 30% mais baixa" -> 70% do volume atual; "baixo" nesta frase é volume, não a faixa
        let alvo = citadas;
        if (/mais baix[ao]/.test(t) && citadas.length > 1) alvo = citadas.filter(f => f !== "baixo");
        const fator = pct !== null ? Math.max(0, 1 - pct) : 0.6;
        alvo.forEach(f => m[f] = {mult: fator});
        frases.push(alvo.map(f => NOME[f]).join(" e ") + " " + Math.round((1 - fator) * 100) + "% mais baixo");
      } else if (sobe) {
        const fator = pct !== null ? 1 + pct : 1.4;
        citadas.forEach(f => m[f] = {mult: fator});
        frases.push(citadas.map(f => NOME[f]).join(" e ") + " " + Math.round((fator - 1) * 100) + "% mais alto");
      } else if (voltar) {
        citadas.forEach(f => m[f] = {set: 1});
        frases.push("voltar " + citadas.map(f => NOME[f]).join(" e "));
      }
      if (Object.keys(m).length) acoes.push({tipo: "faixas", mudancas: m});
    }

    // repetir / duplicar
    const rep = t.match(/\b(repet\w*|duplic\w*|dobra o trecho|copia\w*)\b(?:.*?(\d+)\s*(?:vezes|x))?/);
    if (rep) {
      const n = rep[2] ? Math.min(16, +rep[2]) : 1;
      acoes.push({tipo: "repetir", n}); frases.push(n > 1 ? `repetir ${n} vezes` : "repetir uma vez");
    }

    // apagar os oitos (só quando nenhuma faixa foi citada)
    if (!citadas.length && /\b(apag\w*|remov\w*|delet\w*|exclu\w*|tir\w* (esse|esses|este|estes|isso|o trecho|os oitos)|cort\w* (esse|esses|este|isso|o trecho))\b/.test(t)) {
      acoes.push({tipo: "apagar"}); frases.push("apagar os oitos selecionados");
    }

    return {acoes, frases, faltando, vazio: false};
  }

  // Aplica as ações numa linha do tempo (lista de blocos) nos índices selecionados.
  // Devolve a nova seleção.
  // Curva de volume de um fade (cosseno), amostrada em pontos [x, ganho] dentro de um bloco.
  function curvaFade(dir, iniFade, fimFade, iniBloco, fimBloco) {
    const pts = [];
    const ganho = t => {
      const p = Math.max(0, Math.min(1, (t - iniFade) / (fimFade - iniFade)));
      const sobe = 0.5 - 0.5 * Math.cos(Math.PI * p);
      return dir === "in" ? sobe : 1 - sobe;
    };
    for (let k = 0; k <= 12; k++) {
      const t = iniBloco + (fimBloco - iniBloco) * k / 12;
      pts.push([+(k / 12).toFixed(4), +ganho(t).toFixed(4)]);
    }
    return pts;
  }

  function aplicar(tl, indices, acoes, ctx) {
    let sel = [...indices].sort((a, b) => a - b);
    for (const a of acoes) {
      if (a.tipo === "fade" && ctx && sel.length) {
        const durs = sel.map(i => ctx.dur(tl[i]));
        const total = durs.reduce((x, y) => x + y, 0);
        const L = Math.min(total, a.seg ? a.seg : a.tempos ? a.tempos * ctx.tempo : total);
        const [iniF, fimF] = a.dir === "in" ? [0, L] : [total - L, total];
        let t0 = 0;
        sel.forEach((i, k) => {
          const t1 = t0 + durs[k];
          if (t1 > iniF && t0 < fimF) tl[i].env = curvaFade(a.dir, iniF, fimF, t0, t1);
          else if (a.dir === "in" && t0 >= fimF) delete tl[i].env;
          t0 = t1;
        });
        continue;
      }
      if (a.tipo === "dividir") {
        const novaSel = [];
        let desloc = 0;
        for (const i0 of sel) {
          const i = i0 + desloc, b = tl[i];
          const de = b.de ?? 0, ate = b.ate ?? 1, partes = [];
          for (let k = 0; k < a.partes; k++) {
            const nb = JSON.parse(JSON.stringify(b));
            nb.de = +(de + (ate - de) * k / a.partes).toFixed(5); nb.ate = +(de + (ate - de) * (k + 1) / a.partes).toFixed(5);
            delete nb.env; partes.push(nb);
          }
          tl.splice(i, 1, ...partes);
          for (let k = 0; k < a.partes; k++) novaSel.push(i + k);
          desloc += a.partes - 1;
        }
        sel = novaSel;
        continue;
      }
      if (a.tipo === "faixas") {
        for (const i of sel) for (const [f, m] of Object.entries(a.mudancas)) {
          const atual = tl[i].faixas[f];
          tl[i].faixas[f] = m.set !== undefined ? m.set : Math.max(0, Math.min(2, (atual || 0) * m.mult));
        }
      } else if (a.tipo === "fx") {
        for (const i of sel) {
          tl[i].fx = tl[i].fx || {};
          for (const alvo of a.alvo) tl[i].fx[alvo] = Object.assign({}, tl[i].fx[alvo] || {}, a.fx);
        }
      } else if (a.tipo === "semFx") {
        for (const i of sel) {
          if (!a.alvo) delete tl[i].fx;
          else if (tl[i].fx) { for (const f of a.alvo) delete tl[i].fx[f]; if (!Object.keys(tl[i].fx).length) delete tl[i].fx; }
        }
      } else if (a.tipo === "paradas") {
        for (const i of sel) {
          // tempo N da contagem -> batida N-1 do bloco (blocos cortados começam no meio da contagem)
          const primeiro = Math.round(8 * (tl[i].de ?? 0)), total = Math.round(8 * ((tl[i].ate ?? 1) - (tl[i].de ?? 0)));
          const novas = a.tempos.map(n => n - 1 - primeiro).filter(x => x >= 0 && x < total).map(x => [x, a.dur]);
          const todas = [...(tl[i].paradas || []).filter(p => !novas.some(n => n[0] === p[0])), ...novas].sort((x, y) => x[0] - y[0]);
          if (todas.length) tl[i].paradas = todas;
        }
      } else if (a.tipo === "semParadas") {
        for (const i of sel) delete tl[i].paradas;
      } else if (a.tipo === "semFade") {
        for (const i of sel) delete tl[i].env;
      } else if (a.tipo === "vel") {
        for (const i of sel) tl[i].vel = a.valor;
      } else if (a.tipo === "repetir" && sel.length) {
        // repete o grupo selecionado logo depois dele (contínuo, na ordem)
        const grupo = sel.map(i => JSON.parse(JSON.stringify(tl[i])));
        const pos = sel[sel.length - 1] + 1;
        const novos = [];
        for (let k = 0; k < a.n; k++) novos.push(...grupo.map(b => JSON.parse(JSON.stringify(b))));
        tl.splice(pos, 0, ...novos);
      } else if (a.tipo === "apagar") {
        for (const i of [...sel].reverse()) tl.splice(i, 1);
        sel = [];
      }
    }
    return sel;
  }

  const api = {entender, aplicar, FAIXAS};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.Comandos = api;
})(this);
