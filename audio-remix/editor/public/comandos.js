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
  function entender(texto) {
    const t = semAcento(texto).replace(/\s+/g, " ").trim();
    if (!t) return {acoes: [], frases: [], faltando: [], vazio: true};
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
      [/\b(eco|reverb|delay|distante)\b/, "eco e reverb"],
      [/\b(filtro|abafad|radio|telefone)\w*/, "filtros"],
      [/\b(parada|stop|hit|freeze|silencio no tempo|corte seco no)\b/, "paradas (hits)"],
      [/\b(tom|afina|pitch|mais aguda|mais grave a voz)\b/, "mudar o tom"],
      [/\b(do oito|do trecho|daquele trecho|de outro trecho|que ele usa)\b/, "trazer uma faixa de outro trecho (camadas)"],
      [/\b(house|breaking|locking|popping|krump|waacking|vogue|passinho|funk|dancehall|amapiano|trap|boom ?bap)\b/, "injetar estilo"],
    ];
    for (const [re, nome] of futuros) if (re.test(t)) faltando.push(nome);
    // Uma parte que depende de algo que ainda não existe não mexe em nada (evita fazer pela metade)
    if (faltando.length) return {acoes, frases, faltando};

    const citadas = faixasCitadas(t);
    const pct = porcentagem(t);

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
  function aplicar(tl, indices, acoes) {
    let sel = [...indices].sort((a, b) => a - b);
    for (const a of acoes) {
      if (a.tipo === "faixas") {
        for (const i of sel) for (const [f, m] of Object.entries(a.mudancas)) {
          const atual = tl[i].faixas[f];
          tl[i].faixas[f] = m.set !== undefined ? m.set : Math.max(0, Math.min(2, (atual || 0) * m.mult));
        }
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
