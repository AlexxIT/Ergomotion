# Ergomotion Smart Beds for Home Assistant

[Home Assistant](https://www.home-assistant.io/) custom component for control [Ergomotion Smart Beds](https://eu.ergomotion.com/) via Bluetooth module.

Tested only with **Remote Style B** (check [mobile app](https://play.google.com/store/apps/developer?id=Ergomotion&hl=ru&gl=US)). 

## Installation

[HACS](https://hacs.xyz/) > Integrations > 3 dots (upper top corner) > Custom repositories > URL: `AlexxIT/Ergomotion`, Category: Integration > Add > wait > Jura > Install

Or manually copy `ergomotion` folder from [latest release](https://github.com/AlexxIT/Ergomotion/releases/latest) to `/config/custom_components` folder.

## Configuration

1. Add default [Bluetooth](https://www.home-assistant.io/integrations/bluetooth/) integration. 

2. Configuration > [Integrations](https://my.home-assistant.io/redirect/integrations/) > Add Integration > [Ergomotion Smart Beds](https://my.home-assistant.io/redirect/config_flow_start/?domain=ergomotion)

If you have no MAC address in the setup window, then your HA server can't currently discover any smart bed nearby.

## Bluetooth

Read recommendations here - [Jura Coffee Machines](https://github.com/AlexxIT/Jura).
