-- The rig's stand-in for WirePlumber's ALSA monitor (ORDER 631): there is no sound card in a container, so this
-- creates the ALSA sink nodes of pcm_sa631.c the way monitors/alsa.lua does (createNode): the node's properties go
-- through the configured monitor.alsa.rules with JsonUtils.match_rules_update_properties, then Node("adapter", props).
-- Whatever a package puts in monitor.alsa.rules therefore reaches these nodes by the same code as a real card's.
local rules = Conf.get_section_as_json ("monitor.alsa.rules", Json.Array {})
local log = Log.open_topic ("s-monitors")
rig_nodes = {}
local devices = {
  { "rig_dac",    "sa_dac",    1000, 0 },
  { "rig_only48", "sa_only48",  900, 1 },
  { "rig_pcm16",  "sa_pcm16",   800, 2 },
  { "rig_hdmi",   "sa_hdmi",    700, 3 },
}
-- a Bluetooth-like sink goes through monitor.bluez.rules, as monitors/bluez/create-device.lua applies them
local bt_rules = Conf.get_section_as_json ("monitor.bluez.rules", Json.Array {})
local bt = JsonUtils.match_rules_update_properties (bt_rules, {
    ["factory.name"] = "api.alsa.pcm.sink", ["node.name"] = "bluez_output.rig_bt", ["node.description"] = "rig_bt",
    ["media.class"] = "Audio/Sink", ["device.api"] = "bluez5", ["api.alsa.path"] = "sa_bt", ["api.bluez5.codec"] = "aac", ["api.bluez5.profile"] = "a2dp-sink", ["audio.position"] = "[ FL FR ]",
    ["priority.session"] = 600, ["session.suspend-timeout-seconds"] = 0 })
local btnode = Node ("adapter", bt)
btnode:activate (Features.ALL, function (n, err) if err then log:warning ("rig bt node: " .. tostring (err)) end end)
rig_nodes_bt = btnode
for _, d in ipairs (devices) do
  local props = {
    ["factory.name"] = "api.alsa.pcm.sink",
    ["node.name"] = "alsa_output." .. d[1],
    ["node.nick"] = d[1],
    ["node.description"] = d[1],
    ["media.class"] = "Audio/Sink",
    ["device.api"] = "alsa",
    ["api.alsa.path"] = d[2],
    ["api.alsa.pcm.card"] = d[4],
    ["audio.position"] = "[ FL FR ]",
    ["priority.session"] = d[3],
    ["session.suspend-timeout-seconds"] = 0,
  }
  props = JsonUtils.match_rules_update_properties (rules, props)
  local node = Node ("adapter", props)
  node:activate (Features.ALL, function (n, err)
    if err then log:warning ("rig node " .. d[1] .. ": " .. tostring (err)) end
  end)
  table.insert (rig_nodes, node)
end
