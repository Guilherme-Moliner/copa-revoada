--[[
Copa Revoada — importa o pacote de mídias para a timeline aberta.

Roda de dentro do DaVinci Resolve (gratuito): Workspace > Scripts >
Copa Revoada - importar pacote. Saídas e avisos aparecem em
Workspace > Console.

O que faz:
  1. pega o pacote mais recente gerado por scripts/pacote.py
     (o caminho está em midias/ultimo-pacote.txt);
  2. confere a timeline: 24 fps, igual às peças;
  3. importa as peças para o Media Pool, em IA > Pacote <jogo>;
  4. cria as trilhas de vídeo que faltarem e põe cada peça no quadro e na
     trilha do manifesto.tsv.

Nunca mexe nas trilhas das câmeras (V1, V2 e V3) nem no áudio: os gráficos
começam na V4, a camada gráfica 1. Dá nome às trilhas de gráfico ("Gráfico 1 ·
placar"). Rodar de novo não duplica: peça que já está no mesmo lugar é pulada.

Este arquivo é copiado para a pasta de scripts do Resolve por
scripts/davinci/instala.ps1, que troca __RAIZ__ pela pasta do projeto.
]]

local RAIZ = [[__RAIZ__]]
local FPS = 24
-- V1 a V3 são das câmeras. Nenhuma peça entra abaixo desta trilha, diga o
-- manifesto o que disser.
local MENOR_TRILHA_GRAFICA = 4

local function fala(...) print("[Copa Revoada] " .. string.format(...)) end
local feito = {}       -- o que já mudou no projeto, para contar se parar no meio
local function relata()
  if #feito == 0 and not feito.postas then
    fala("nada foi mudado no projeto até aqui.")
    return
  end
  fala("o que já tinha sido feito:")
  for _, f in ipairs(feito) do print("    - " .. f) end
  if feito.postas then print("    - pôs " .. feito.postas .. " peças na timeline") end
  fala("rodar de novo é seguro: o que já está no lugar é pulado.")
end
local function para(...) fala(...); relata(); error("parado", 0) end

local function le(caminho)
  local f = io.open(caminho, "r")
  if not f then return nil end
  local t = f:read("*a"); f:close()
  return t
end

local function apara(s) return (s:gsub("^%s+", ""):gsub("%s+$", "")) end

local function divide(linha, sep)
  local out = {}
  for campo in (linha .. sep):gmatch("(.-)" .. sep) do out[#out + 1] = campo end
  return out
end

-- As funções do Resolve que devolvem lista trazem, em algumas versões (a
-- 19.0 beta, por exemplo), números misturados aos objetos na mesma tabela. Ler
-- a tabela inteira fazia o script tratar um desses números como pasta e parar
-- ("attempt to index local 'f' (a number value)"). Toda lista vinda do Resolve
-- passa por aqui, e só os objetos seguem.
local function objetos(t)
  local out = {}
  if type(t) ~= "table" then return out end
  for _, v in pairs(t) do
    if type(v) == "userdata" or type(v) == "table" then out[#out + 1] = v end
  end
  return out
end

-- Em que ponto o script está, e o que já mudou no projeto: se algo der errado,
-- é isso que aparece no Console, em vez de um erro de Lua.
local etapa = "começo"
local postas = 0

local ok, erro = pcall(function()
  local resolve = resolve or Resolve()
  if not resolve then para("não achei o Resolve. Rode por Workspace > Scripts.") end

  -- 1. o pacote
  etapa = "ler o pacote (midias\\ultimo-pacote.txt e manifesto.tsv)"
  local ponteiro = le(RAIZ .. [[\midias\ultimo-pacote.txt]])
  if not ponteiro then para("não achei midias\\ultimo-pacote.txt: gere o pacote antes (scripts\\pacote.py gerar).") end
  local pasta = apara(ponteiro)
  local texto = le(pasta .. [[\manifesto.tsv]])
  if not texto then para("não achei o manifesto em %s", pasta) end
  local jogo = pasta:match("([^\\/]+)$")

  local linhas, cab = {}, nil
  for linha in texto:gmatch("[^\r\n]+") do
    local c = divide(linha, "\t")
    if not cab then
      cab = {}
      for i, nome in ipairs(c) do cab[nome] = i end
    else
      linhas[#linhas + 1] = {
        lance = c[cab.lance], peca = c[cab.peca], arquivo = c[cab.arquivo], tipo = c[cab.tipo],
        quadro = tonumber(c[cab.quadro]), duracao = tonumber(c[cab.duracao]),
        trilha = tonumber(c[cab.trilha]), timecode = c[cab.timecode],
        camada = cab.camada and tonumber(c[cab.camada]) or nil,
        camada_nome = cab.camada_nome and c[cab.camada_nome] or nil,
      }
    end
  end
  if #linhas == 0 then para("o manifesto de %s está vazio.", jogo) end

  -- 2. a timeline
  etapa = "conferir o projeto e a timeline abertos"
  local projeto = resolve:GetProjectManager():GetCurrentProject()
  if not projeto then para("abra o projeto antes de rodar o script.") end
  local tl = projeto:GetCurrentTimeline()
  if not tl then para("abra a timeline antes de rodar o script.") end
  local fps = tonumber(tl:GetSetting("timelineFrameRate"))
  if not fps or math.abs(fps - FPS) > 0.01 then
    para("a timeline \"%s\" está a %s fps e as peças são de %d fps. Sem bater, cada peça cairia no lugar errado.",
         tl:GetName(), tostring(tl:GetSetting("timelineFrameRate")), FPS)
  end
  local inicio = tl:GetStartFrame()
  fala("pacote %s · %d peças · timeline \"%s\" começa no quadro %d", jogo, #linhas, tl:GetName(), inicio)

  local maior = 0
  for _, l in ipairs(linhas) do
    if not l.trilha or l.trilha < MENOR_TRILHA_GRAFICA then
      para("a peça %s pede a trilha V%s, mas V1 a V%d são das câmeras e não são tocadas.",
           l.arquivo, tostring(l.trilha), MENOR_TRILHA_GRAFICA - 1)
    end
    if l.trilha > maior then maior = l.trilha end
  end

  -- 3. Media Pool: IA > Pacote <jogo>
  etapa = "achar ou criar a pasta IA > Pacote " .. jogo .. " no Media Pool"
  local mp = projeto:GetMediaPool()
  if not mp then para("o Resolve não devolveu o Media Pool do projeto.") end
  local function subpasta(mae, nome)
    for _, f in ipairs(objetos(mae:GetSubFolderList())) do
      if f:GetName() == nome then return f end
    end
    local nova = mp:AddSubFolder(mae, nome)
    if type(nova) ~= "userdata" and type(nova) ~= "table" then
      para("o Resolve não criou a pasta \"%s\" no Media Pool.", nome)
    end
    feito[#feito + 1] = "criou a pasta \"" .. nome .. "\" no Media Pool"
    return nova
  end
  local raiz = mp:GetRootFolder()
  if not raiz then para("o Resolve não devolveu a pasta raiz do Media Pool.") end
  local ia = subpasta(raiz, "IA")
  local destino = subpasta(ia, "Pacote " .. jogo)
  mp:SetCurrentFolder(destino)

  etapa = "importar as peças para o Media Pool"
  local itens = {}
  for _, it in ipairs(objetos(destino:GetClipList())) do itens[it:GetName()] = it end
  local faltam, vistos = {}, {}
  for _, l in ipairs(linhas) do
    if not itens[l.arquivo] and not vistos[l.arquivo] then
      faltam[#faltam + 1] = pasta .. "\\" .. l.arquivo
      vistos[l.arquivo] = true
    end
  end
  if #faltam > 0 then
    local vindos = objetos(mp:ImportMedia(faltam))
    for _, it in ipairs(vindos) do itens[it:GetName()] = it end
    feito[#feito + 1] = "importou " .. #vindos .. " de " .. #faltam .. " arquivos para o Media Pool"
  end

  -- 4. trilhas e posições
  etapa = "criar e nomear as trilhas de gráfico"
  local antes = tl:GetTrackCount("video")
  while tl:GetTrackCount("video") < maior do
    local n = tl:GetTrackCount("video")
    tl:AddTrack("video")
    if tl:GetTrackCount("video") <= n then para("o Resolve não criou a trilha V%d.", n + 1) end
  end
  if tl:GetTrackCount("video") > antes then
    feito[#feito + 1] = "criou as trilhas V" .. (antes + 1) .. " a V" .. maior
  end

  -- nome nas trilhas de gráfico; trilha que alguém já batizou não é renomeada
  local nomeDe = {}
  for _, l in ipairs(linhas) do
    if l.camada and not nomeDe[l.trilha] then
      nomeDe[l.trilha] = "Gráfico " .. l.camada .. ((l.camada_nome and l.camada_nome ~= "") and (" · " .. l.camada_nome) or "")
    end
  end
  for t, nome in pairs(nomeDe) do
    local okNome, atual = pcall(function() return tl:GetTrackName("video", t) end)
    if okNome and (atual == nil or atual == "" or atual == ("Video " .. t) or atual == ("V" .. t)) then
      pcall(function() tl:SetTrackName("video", t, nome) end)
    end
  end

  etapa = "pôr as peças na timeline"
  local ja = {}
  for t = MENOR_TRILHA_GRAFICA, maior do
    for _, it in ipairs(objetos(tl:GetItemListInTrack("video", t))) do
      ja[t .. ":" .. it:GetStart()] = true
    end
  end

  local puladas, curtas, fora_do_lugar = 0, 0, 0
  local function poe(item, trilha, quadro, dur)
    local r = mp:AppendToTimeline({{
      mediaPoolItem = item, startFrame = 0, endFrame = dur - 1,
      trackIndex = trilha, recordFrame = quadro, mediaType = 1,
    }})
    return objetos(r)[1]
  end

  for _, l in ipairs(linhas) do
    local item = itens[l.arquivo]
    local quadro = inicio + l.quadro
    if not item then
      fala("! não consegui importar %s", l.arquivo)
    elseif ja[l.trilha .. ":" .. quadro] then
      puladas = puladas + 1
    else
      local posta = poe(item, l.trilha, quadro, l.duracao)
      if not posta then
        fala("! o Resolve recusou %s em V%d, %s", l.arquivo, l.trilha, l.timecode)
      elseif posta:GetStart() ~= quadro then
        -- versão do Resolve que ignora a posição pedida: a peça foi parar em
        -- outro lugar. Não segue empilhando peças erradas.
        fora_do_lugar = fora_do_lugar + 1
        postas = postas + 1
        feito.postas = postas
        para("o Resolve pôs %s no quadro %d, e o pedido era %d (%s). Esta versão não respeita a "
             .. "posição pedida: apague essa peça da V%d e me mande estas linhas.",
             l.arquivo, posta:GetStart(), quadro, l.timecode, l.trilha)
      else
        -- imagem parada: se o Resolve limitar a duração, completa emendando
        -- cópias até cobrir o trecho inteiro
        local cobre = posta:GetDuration()
        if cobre < l.duracao then
          curtas = curtas + 1
          while cobre < l.duracao do
            local p = poe(item, l.trilha, quadro + cobre, math.min(cobre > 0 and cobre or l.duracao, l.duracao - cobre))
            if not p or p:GetDuration() <= 0 then break end
            cobre = cobre + p:GetDuration()
          end
        end
        postas = postas + 1
        feito.postas = postas
      end
    end
  end

  fala("pronto: %d peças postas, %d já estavam no lugar.", postas, puladas)
  if curtas > 0 then
    fala("%d imagens paradas foram emendadas em pedaços porque o Resolve limitou a duração delas.", curtas)
  end
end)

if not ok and erro ~= "parado" then
  print("[Copa Revoada] parou com um erro na etapa: " .. etapa .. ".")
  print("[Copa Revoada] o que o Resolve respondeu: " .. tostring(erro))
  relata()
  print("[Copa Revoada] copie estas linhas e mande para o Claude.")
end
