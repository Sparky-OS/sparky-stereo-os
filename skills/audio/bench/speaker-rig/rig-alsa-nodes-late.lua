rig_delay_ms = 6000
-- The speaker rig's stand-in for WirePlumber's ALSA monitor (ORDER 23): no sound card in a container, so the ALSA
-- sink nodes of pcm_sa631.c are made the way monitors/alsa.lua does (createNode): the properties go through the
-- configured monitor.alsa.rules, then Node("adapter", props). A 5.1 card, a 7.1 card and a stereo card, each with the
-- channel map of its current profile in audio.position.
-- A card leaves with `pw-cli destroy ID` and comes back with `pw-cli create-node adapter` (see case.py); the lua of WirePlumber has no
-- file access. rig-alsa-nodes-late.lua sets rig_delay_ms = 6000 and loads this script's body: every node appears six seconds after the
-- start, so a device shows up after the modules PipeWire loads at its start.
local rules = Conf.get_section_as_json ("monitor.alsa.rules", Json.Array {})
local log = Log.open_topic ("s-monitors")
rig_nodes = {}
local devices = {
  { "rig_51", "sa_51", "[ FL FR FC LFE RL RR ]", 6, 1000 },
  { "rig_71", "sa_71", "[ FL FR FC LFE RL RR SL SR ]", 8, 900 },
  { "rig_st", "sa_st", "[ FL FR ]", 2, 800 },
}
local function create (d)
  local props = {
    ["factory.name"] = "api.alsa.pcm.sink",
    ["node.name"] = "alsa_output." .. d[1],
    ["node.nick"] = d[1],
    ["node.description"] = d[1],
    ["media.class"] = "Audio/Sink",
    ["device.api"] = "alsa",
    ["api.alsa.path"] = d[2],
    ["audio.channels"] = d[4],
    ["audio.position"] = d[3],
    ["priority.session"] = d[5],
    ["session.suspend-timeout-seconds"] = 0,
  }
  props = JsonUtils.match_rules_update_properties (rules, props)
  local node = Node ("adapter", props)
  node:activate (Features.ALL, function (n, err)
    if err then log:warning ("rig node " .. d[1] .. ": " .. tostring (err)) end
  end)
  rig_nodes[d[1]] = node
end
local delay = tonumber (rig_delay_ms) or 0
if delay > 0 then
  -- the card appears after the modules PipeWire loaded at its start
  Core.timeout_add (delay, function ()
    for _, d in ipairs (devices) do create (d) end
    return false
  end)
else
  for _, d in ipairs (devices) do create (d) end
end
