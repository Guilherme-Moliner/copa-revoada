/**
 * Copa Revoada — ponte entre o app e a planilha.
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
    if (acao === 'ler')   return json(ler(e.parameter.jogo));
    if (acao === 'jogos') return json({ok: true, jogos: listaJogos()});
    return json({ok: false, erro: 'ação desconhecida: ' + acao});
  } catch (err) {
    return json({ok: false, erro: String(err)});
  }
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

/** Cria a aba do jogo se ela ainda não existe, com uma chave nova. */
function abaOuCria(jogo) {
  var ss = SpreadsheetApp.getActive();
  var ws = ss.getSheetByName(PREFIXO + jogo);
  if (ws) return ws;
  ws = ss.insertSheet(PREFIXO + jogo);
  ws.getRange('A1').setValue(
    'Lances marcados deste jogo. O app grava e lê daqui. ' +
    'A chave abaixo é o que libera a edição no app — trate como senha do grupo.');
  ws.getRange('A2').setValue('chave_de_acesso');
  ws.getRange('B2').setValue(novaChave());
  ws.getRange('A4:G4').setValues([['min','time','tipo','jogador','xg','por','em']]);
  ws.setFrozenRows(4);
  return ws;
}

function novaChave() {
  var alfa = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789', a = '', b = '';
  for (var i = 0; i < 4; i++) a += alfa.charAt(Math.floor(Math.random() * alfa.length));
  for (var j = 0; j < 4; j++) b += alfa.charAt(Math.floor(Math.random() * alfa.length));
  return 'RVD-' + a + '-' + b;
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
  var jogo = corpo.jogo;
  var ws = abaOuCria(jogo);
  var esperada = String(ws.getRange('B2').getValue() || '').trim();
  var recebida = String(corpo.chave || '').trim();
  if (!esperada) return {ok: false, erro: 'esta aba está sem chave; preencha a célula B2'};
  if (recebida.toUpperCase() !== esperada.toUpperCase()) {
    return {ok: false, erro: 'chave não confere'};
  }

  var eventos = corpo.eventos || [];
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
