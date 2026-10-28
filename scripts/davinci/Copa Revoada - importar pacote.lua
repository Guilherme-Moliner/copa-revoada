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

Nunca mexe na V1 nem no áudio. Rodar de novo não duplica: peça que já está no
mesmo lugar é pulada.

Este arquivo é copiado para a pasta de scripts do Resolve por
scripts/davinci/instala.ps1, que troca __RAIZ__ pela pasta do projeto.
]]

local RAIZ = [[__RAIZ__]]
local FPS = 24

local function fala(...) print("[Copa Revoada] " .. string.format(...)) end
local function para(...) fala(...); fala("nada foi alterado na timeline."); error("parado", 0) end

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

local ok, erro = pcall(function()
  local resolve = resolve or Resolve()
  if not resolve then para("não achei o Resolve. Rode por Workspace > Scripts.") end

  -- 1. o pacote
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
      }
    end
  end
  if #linhas == 0 then para("o manifesto de %s está vazio.", jogo) end

  -- 2. a timeline
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
    if not l.trilha or l.trilha < 2 then para("a peça %s pede a trilha %s: a V1 é do jogo e não é tocada.", l.arquivo, tostring(l.trilha)) end
    if l.trilha > maior then maior = l.trilha end
  end

  -- 3. Media Pool: IA > Pacote <jogo>
  local mp = projeto:GetMediaPool()
  local function subpasta(mae, nome)
    for _, f in pairs(mae:GetSubFolderList() or {}) do
      if f:GetName() == nome then return f end
    end
    return mp:AddSubFolder(mae, nome)
  end
  local ia = subpasta(mp:GetRootFolder(), "IA")
  local destino = subpasta(ia, "Pacote " .. jogo)
  mp:SetCurrentFolder(destino)

  local itens = {}
  for _, it in pairs(destino:GetClipList() or {}) do itens[it:GetName()] = it end
  local faltam, vistos = {}, {}
  for _, l in ipairs(linhas) do
    if not itens[l.arquivo] and not vistos[l.arquivo] then
      faltam[#faltam + 1] = pasta .. "\\" .. l.arquivo
      vistos[l.arquivo] = true
    end
  end
  if #faltam > 0 then
    for _, it in pairs(mp:ImportMedia(faltam) or {}) do itens[it:GetName()] = it end
  end

  -- 4. trilhas e posições
  while tl:GetTrackCount("video") < maior do tl:AddTrack("video") end

  local ja = {}
  for t = 2, maior do
    for _, it in pairs(tl:GetItemListInTrack("video", t) or {}) do
      ja[t .. ":" .. it:GetStart()] = true
    end
  end

  local postas, puladas, curtas = 0, 0, 0
  local function poe(item, trilha, quadro, dur)
    local r = mp:AppendToTimeline({{
      mediaPoolItem = item, startFrame = 0, endFrame = dur - 1,
      trackIndex = trilha, recordFrame = quadro, mediaType = 1,
    }})
    return r and r[1]
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
      else
        -- imagem parada: se o Resolve limitar a duração, completa emendando
        -- cópias até cobrir o trecho inteiro
        local feito = posta:GetDuration()
        if feito < l.duracao then
          curtas = curtas + 1
          while feito < l.duracao do
            local p = poe(item, l.trilha, quadro + feito, math.min(feito > 0 and feito or l.duracao, l.duracao - feito))
            if not p or p:GetDuration() <= 0 then break end
            feito = feito + p:GetDuration()
          end
        end
        postas = postas + 1
      end
    end
  end

  fala("pronto: %d peças postas, %d já estavam no lugar.", postas, puladas)
  if curtas > 0 then
    fala("%d imagens paradas foram emendadas em pedaços porque o Resolve limitou a duração delas.", curtas)
  end
end)

if not ok and erro ~= "parado" then
  print("[Copa Revoada] erro inesperado: " .. tostring(erro))
end
