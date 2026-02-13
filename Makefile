:PHONY new-device
new-device:
	mosquitto_pub -t "zigbee2mqtt/bridge/request/permit_join" -m '{"value":true, "time":120}' -p 1889
