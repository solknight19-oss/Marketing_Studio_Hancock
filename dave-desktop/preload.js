const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('DaveDesktop', {
  getStatus: () => ipcRenderer.invoke('dave-desktop:get-status'),
  show: () => ipcRenderer.invoke('dave-desktop:show'),
  startLiveMic: () => ipcRenderer.invoke('dave-desktop:start-live-mic'),
  standby: () => ipcRenderer.invoke('dave-desktop:standby')
});
