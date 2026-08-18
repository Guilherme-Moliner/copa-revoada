/**
 * Copa Revoada — ponte entre o app e a planilha.
 *
 * ATENÇÃO: a chave de cada jogo mora na célula B2 da aba daquele jogo, na
 * planilha do Google. O .xlsx deste repositório é público, então lá a B2 vem
 * com um marcador. Digite a chave de verdade só depois de subir pro Drive.
 *
 * Cole este arquivo em Extensões > Apps Script da planilha e publique como
 * Web App. O passo a passo está em docs/planilha-colaborativa.md.
 *
 * O app é um site estático, sem servidor. Este script é o único pedaço que
 * roda do lado da planilha, e é ele que decide quem pode escrever.
 *
 * Ler é livre. Escrever exige a chave que está na célula B2 da aba do jogo —
 * a mesma que aparece na planilha. A chave NUNCA fica no código do site:
 * quem for marcar lance digita na hora.
 */

var PREFIXO = 'LANCES ';

function doGet(e) {
  var acao = (e.parameter.acao || 'ler');
  try {
    if (acao === 'ler')      return json(ler(e.parameter.jogo));
    if (acao === 'jogos')    return json({ok: true, jogos: listaJogos()});
    if (acao === 'planilha') return json(planilhaInteira());
    return json({ok: false, erro: 'ação desconhecida: ' + acao});
  } catch (err) {
    return json({ok: false, erro: String(err)});
  }
}

/**
 * Devolve as abas da planilha como JSON: {NOME_DA_ABA: [[linha], [linha]…]}.
 *
 * É assim que o site passa a ler os dados daqui em vez do arquivo do
 * repositório. A planilha é privada, então a URL de export do Sheets
 * devolveria 401 para quem estivesse de fora.
 *
 * Lê direto com SpreadsheetApp de propósito: buscar o .xlsx com
 * UrlFetchApp exigiria a permissão de chamada externa, e uma permissão a
 * mais para autorizar de novo. Aqui basta a permissão da própria planilha,
 * que o script já tem.
 *
 * As abas de lances não vêm no pacote: elas podem crescer muito e quem
 * precisa delas usa a ação "ler", que já existe.
 */
function planilhaInteira() {
  var ss = SpreadsheetApp.getActive();
  var abas = {};
  ss.getSheets().forEach(function (ws) {
    var nome = ws.getName();
    if (nome.indexOf(PREFIXO) === 0) return;      // LANCES ... fica de fora
    if (nome === 'CONFIG') return;                 // a chave não sai daqui
    var ultima = ws.getLastRow(), colunas = ws.getLastColumn();
    if (!ultima || !colunas) { abas[nome] = []; return; }
    abas[nome] = ws.getRange(1, 1, ultima, colunas).getValues().map(function (linha) {
      return linha.map(function (v) {
        if (v === '' || v === null) return null;
        if (v instanceof Date) {
          return Utilities.formatDate(v, Session.getScriptTimeZone() || 'America/Sao_Paulo',
                                      'yyyy-MM-dd');
        }
        return v;
      });
    });
  });
  return {ok: true, nome: ss.getName(), abas: abas};
}

function doPost(e) {
  try {
    var corpo = JSON.parse(e.postData.contents || '{}');
    if (corpo.acao === 'gravar') return json(gravar(corpo));
    return json({ok: false, erro: 'ação desconhecida'});
  } catch (err) {
    return json({ok: false, erro: String(err)});
  }
}

/* ------------------------------------------------------------------ */

function aba(jogo) {
  if (!jogo) throw 'faltou dizer qual jogo';
  return SpreadsheetApp.getActive().getSheetByName(PREFIXO + jogo);
}

/** Chave mestra: fica na aba CONFIG, célula B2. É ela que autoriza criar a
 *  aba de um jogo novo. Sem isso, quem tivesse a URL criaria aba à vontade. */
function chaveMestra() {
  var ws = SpreadsheetApp.getActive().getSheetByName('CONFIG');
  return ws ? String(ws.getRange('B2').getValue() || '').trim() : '';
}

/** Só aceita id de jogo no formato AAAA-MM e que exista na aba JOGOS.
 *  Sem isso, o nome da aba viria do lado de fora sem nenhum controle. */
function jogoValido(jogo) {
  if (!/^\d{4}-\d{2}$/.test(String(jogo || ''))) return false;
  var ws = SpreadsheetApp.getActive().getSheetByName('JOGOS');
  if (!ws) return false;
  var ids = ws.getRange(4, 1, Math.max(ws.getLastRow() - 3, 1), 1).getValues();
  for (var i = 0; i < ids.length; i++) {
    if (String(ids[i][0] || '').trim() === jogo) return true;
  }
  return false;
}

function criaAba(jogo, chave) {
  var ss = SpreadsheetApp.getActive();
  var ws = ss.insertSheet(PREFIXO + jogo);
  ws.getRange('A1').setValue(
    'Lances marcados deste jogo. O app grava e lê daqui. ' +
    'A chave abaixo é o que libera a edição no app — trate como senha do grupo.');
  ws.getRange('A2').setValue('chave_de_acesso');
  ws.getRange('B2').setValue(chave);
  ws.getRange('A4:G4').setValues([['min','time','tipo','jogador','xg','por','em']]);
  ws.setFrozenRows(4);
  return ws;
}

function listaJogos() {
  return SpreadsheetApp.getActive().getSheets()
    .map(function (s) { return s.getName(); })
    .filter(function (n) { return n.indexOf(PREFIXO) === 0; })
    .map(function (n) { return n.slice(PREFIXO.length); });
}

/** Leitura é livre: qualquer um do grupo abre o app e vê o que já foi marcado. */
function ler(jogo) {
  var ws = aba(jogo);
  if (!ws) return {ok: true, jogo: jogo, eventos: [], existe: false};
  var ultima = ws.getLastRow();
  var eventos = [];
  if (ultima >= 5) {
    ws.getRange(5, 1, ultima - 4, 7).getValues().forEach(function (l) {
      if (l[0] === '' && l[3] === '') return;
      eventos.push({
        min: Number(l[0]) || 0, t: String(l[1] || 'A'), tipo: String(l[2] || ''),
        j: String(l[3] || ''), xg: Number(l[4]) || 0,
        por: String(l[5] || ''), em: l[6] ? String(l[6]) : ''
      });
    });
  }
  return {ok: true, jogo: jogo, eventos: eventos, existe: true};
}

/**
 * Grava a lista inteira de uma vez: o app manda o estado completo daquele
 * jogo e a aba passa a refletir exatamente isso. Assim duas pessoas editando
 * não geram linha duplicada — a última gravação vale, e quem gravou fica
 * registrado na coluna "por".
 */
function gravar(corpo) {
  var jogo = String(corpo.jogo || '').trim();
  var recebida = String(corpo.chave || '').trim();

  /* A conferência da chave vem ANTES de qualquer escrita, inclusive antes de
     criar aba. Na primeira versão eu criava a aba primeiro e conferia depois,
     e com isso qualquer um com a URL criava aba sem chave nenhuma. */
  if (!recebida) return {ok: false, erro: 'faltou a chave'};
  if (!jogoValido(jogo)) {
    return {ok: false, erro: 'jogo desconhecido: use um id que exista na aba JOGOS'};
  }

  var ss = SpreadsheetApp.getActive();
  var ws = ss.getSheetByName(PREFIXO + jogo);

  /* UMA chave resolve tudo: a da aba CONFIG. A B2 de cada jogo é opcional e
     só existe para quem quiser uma chave diferente num jogo específico —
     qualquer uma das duas é aceita. */
  var geral = chaveMestra();
  var confere = function (guardada) {
    return guardada && guardada !== 'TROQUE-ESTA-CHAVE' &&
           recebida.toUpperCase() === guardada.toUpperCase();
  };

  if (ws) {
    var doJogo = String(ws.getRange('B2').getValue() || '').trim();
    if (!confere(doJogo) && !confere(geral)) {
      if ((!doJogo || doJogo === 'TROQUE-ESTA-CHAVE') && !geral) {
        return {ok: false, erro: 'nenhuma chave definida: preencha a B2 desta aba ou a da aba CONFIG'};
      }
      return {ok: false, erro: 'chave não confere'};
    }
  } else {
    /* Aba nova só nasce com a chave geral: sem isso, quem tivesse a URL
       criaria aba à vontade. Ela nasce herdando essa mesma chave. */
    if (!confere(geral)) {
      return {ok: false, erro: geral
        ? 'para criar a aba de um jogo novo, use a chave da aba CONFIG'
        : 'crie a aba CONFIG com a chave na célula B2 para o app poder abrir jogos novos'};
    }
    ws = criaAba(jogo, geral);
  }

  var eventos = corpo.eventos || [];
  if (!Array.isArray(eventos)) return {ok: false, erro: 'lista de lances inválida'};
  if (eventos.length > 500) return {ok: false, erro: 'lances demais numa gravação só'};
  var quem = String(corpo.por || 'sem nome').slice(0, 40);
  var agora = Utilities.formatDate(new Date(),
    Session.getScriptTimeZone() || 'America/Sao_Paulo', 'dd/MM HH:mm');

  var ultima = ws.getLastRow();
  if (ultima >= 5) ws.getRange(5, 1, ultima - 4, 7).clearContent();

  if (eventos.length) {
    var linhas = eventos.map(function (ev) {
      return [ev.min, ev.t, ev.tipo, ev.j, ev.xg, ev.por || quem, ev.em || agora];
    });
    linhas.sort(function (a, b) { return a[0] - b[0]; });
    ws.getRange(5, 1, linhas.length, 7).setValues(linhas);
  }
  return {ok: true, gravados: eventos.length, jogo: jogo, em: agora};
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
