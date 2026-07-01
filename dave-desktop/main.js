const { app, BrowserWindow, Menu, Tray, ipcMain, nativeImage, shell, session, globalShortcut } = require('electron');
const { spawn, execFile } = require('child_process');
const fs = require('fs');
const http = require('http');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..');
const appDataDir = path.join(projectRoot, 'app_data');
const port = Number(process.env.PORT || 8772);
const host = process.env.HOST || '127.0.0.1';
const baseUrl = `http://127.0.0.1:${port}`;
const daveUrl = `${baseUrl}/dave-local`;
const healthUrl = `${baseUrl}/healthz`;
const expectedInteractionVersion = 'dave_stt_fallback_v10';
const logFile = path.join(appDataDir, 'dave_electron.log');

let mainWindow = null;
let tray = null;
let serverProcess = null;
let lastHealth = null;

function log(message) {
  fs.mkdirSync(appDataDir, { recursive: true });
  fs.appendFileSync(logFile, `[${new Date().toISOString()}] ${message}\n`, 'utf8');
}

function readSecret(relativePath) {
  try {
    const value = fs.readFileSync(path.resolve(projectRoot, relativePath), 'utf8').trim();
    return value || '';
  } catch (_error) {
    return '';
  }
}

function serverEnv() {
  const env = {
    ...process.env,
    HOST: host,
    PORT: String(port),
    APP_DATA_DIR: appDataDir,
    DAVE_LOCAL_AUTO_LOGIN: '1',
    DAVE_ELEVENLABS_VOICE_NAME: process.env.DAVE_ELEVENLABS_VOICE_NAME || 'Jarvis 1.1 Voice',
    DAVE_ELEVENLABS_FALLBACK_VOICE_ID: process.env.DAVE_ELEVENLABS_FALLBACK_VOICE_ID || '6Lopt6P83rUsEz3TeM5C',
    DAVE_ELEVENLABS_FALLBACK_VOICE_NAME: process.env.DAVE_ELEVENLABS_FALLBACK_VOICE_NAME || 'Jarvis'
  };

  if (!env.ELEVENLABS_API_KEY) {
    env.ELEVENLABS_API_KEY = readSecret('../Hancock_CoPilot/elevenlabs_key.txt');
  }
  if (!env.ANTHROPIC_API_KEY) {
    env.ANTHROPIC_API_KEY = readSecret('../Hancock_CoPilot/anthropic_key.txt');
  }
  if (!env.OPENAI_API_KEY) {
    env.OPENAI_API_KEY = readSecret('../Hancock_CoPilot/openai_key.txt');
  }
  return env;
}

function getJson(url, timeoutMs = 2500) {
  return new Promise((resolve, reject) => {
    const request = http.get(url, { timeout: timeoutMs }, (response) => {
      let body = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { body += chunk; });
      response.on('end', () => {
        try {
          resolve({ statusCode: response.statusCode, data: JSON.parse(body) });
        } catch (error) {
          reject(error);
        }
      });
    });
    request.on('timeout', () => {
      request.destroy(new Error('Dave health check timed out.'));
    });
    request.on('error', reject);
  });
}

async function readHealth() {
  const result = await getJson(healthUrl);
  lastHealth = result.data;
  return result.data;
}

function healthIsCurrent(health) {
  return Boolean(
    health &&
    health.ok &&
    health.dave &&
    health.dave.interaction_version === expectedInteractionVersion
  );
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function stopPortIfStale() {
  return new Promise((resolve) => {
    execFile('lsof', ['-tiTCP:' + port, '-sTCP:LISTEN'], (error, stdout) => {
      if (error || !stdout.trim()) {
        resolve();
        return;
      }
      const pids = stdout.trim().split(/\s+/).filter(Boolean);
      if (!pids.length) {
        resolve();
        return;
      }
      log(`Stopping stale Dave service on port ${port}: ${pids.join(', ')}`);
      execFile('kill', pids, () => {
        setTimeout(resolve, 1200);
      });
    });
  });
}

function spawnServer() {
  fs.mkdirSync(appDataDir, { recursive: true });
  const out = fs.openSync(path.join(appDataDir, 'dave_server.log'), 'a');
  serverProcess = spawn('python3', ['-u', 'server.py'], {
    cwd: projectRoot,
    env: serverEnv(),
    stdio: ['ignore', out, out],
    detached: true
  });

  serverProcess.on('exit', (code, signal) => {
    log(`Dave server exited: code=${code || ''} signal=${signal || ''}`);
    serverProcess = null;
  });
  log(`Started Dave server pid=${serverProcess.pid}`);
  serverProcess.unref();
}

async function ensureServer() {
  try {
    const health = await readHealth();
    if (healthIsCurrent(health)) {
      return health;
    }
    log(`Dave health version mismatch. Restarting local service.`);
    await stopPortIfStale();
  } catch (_error) {
    // Server is not responding yet.
  }

  if (!serverProcess) {
    spawnServer();
  }

  for (let attempt = 0; attempt < 24; attempt += 1) {
    await wait(500);
    try {
      const health = await readHealth();
      if (healthIsCurrent(health)) {
        return health;
      }
    } catch (_error) {
      // Keep waiting.
    }
  }
  throw new Error('Dave did not come online.');
}

function configurePermissions() {
  app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    const url = webContents.getURL() || '';
    const localDave = url.startsWith(baseUrl);
    const allowed = localDave && ['media', 'microphone', 'notifications'].includes(permission);
    callback(Boolean(allowed));
  });
  session.defaultSession.setPermissionCheckHandler((_webContents, permission, requestingOrigin) => {
    const localDave = String(requestingOrigin || '').startsWith(baseUrl);
    return Boolean(localDave && ['media', 'microphone', 'notifications'].includes(permission));
  });
}

function createWindow() {
  log('Creating Dave Desktop window.');
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1120,
    minHeight: 720,
    title: 'Dave Desktop',
    backgroundColor: '#02070A',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      webSecurity: true
    }
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  mainWindow.loadURL(daveUrl);
}

function showDave() {
  if (!mainWindow) {
    createWindow();
    return;
  }
  if (mainWindow.isMinimized()) {
    mainWindow.restore();
  }
  mainWindow.show();
  mainWindow.focus();
}

function runDaveScript(script) {
  if (!mainWindow) {
    showDave();
    return;
  }
  mainWindow.webContents.executeJavaScript(script).catch((error) => {
    log(`Dave script failed: ${error.message}`);
  });
}

function createTray() {
  const image = nativeImage.createEmpty();
  tray = new Tray(image);
  tray.setToolTip('Dave Desktop');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Show Dave', click: showDave },
    { label: 'Start Live Mic', click: () => runDaveScript('window.startConversation && window.startConversation();') },
    { label: 'Open Dave in Browser', click: () => shell.openExternal(daveUrl) },
    { type: 'separator' },
    { label: 'Standby', click: () => runDaveScript('window.stopVoice && window.stopVoice();') },
    { label: 'Reload Dave', click: () => mainWindow && mainWindow.reload() },
    { type: 'separator' },
    { label: 'Quit Dave Desktop', click: () => app.quit() }
  ]));
}

function createMenu() {
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    {
      label: 'Dave',
      submenu: [
        { label: 'Show Dave', accelerator: 'CommandOrControl+Shift+D', click: showDave },
        { label: 'Start Live Mic', accelerator: 'CommandOrControl+Shift+M', click: () => runDaveScript('window.startConversation && window.startConversation();') },
        { label: 'Open Dave in Browser', click: () => shell.openExternal(daveUrl) },
        { type: 'separator' },
        { label: 'Standby', click: () => runDaveScript('window.stopVoice && window.stopVoice();') },
        { label: 'Reload', role: 'reload' },
        { type: 'separator' },
        { label: 'Quit', role: 'quit' }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' }
      ]
    }
  ]));
}

ipcMain.handle('dave-desktop:get-status', async () => {
  try {
    return { ok: true, health: await readHealth(), url: daveUrl };
  } catch (error) {
    return { ok: false, error: error.message, health: lastHealth, url: daveUrl };
  }
});

ipcMain.handle('dave-desktop:show', () => {
  showDave();
  return { ok: true };
});

ipcMain.handle('dave-desktop:start-live-mic', () => {
  runDaveScript('window.startConversation && window.startConversation();');
  return { ok: true };
});

ipcMain.handle('dave-desktop:standby', () => {
  runDaveScript('window.stopVoice && window.stopVoice();');
  return { ok: true };
});

app.whenReady().then(async () => {
  log('Dave Desktop starting.');
  configurePermissions();
  createMenu();
  createTray();
  await ensureServer();
  createWindow();
  globalShortcut.register('CommandOrControl+Shift+D', showDave);
  globalShortcut.register('CommandOrControl+Shift+M', () => runDaveScript('window.startConversation && window.startConversation();'));
});

app.on('activate', () => {
  showDave();
});

app.on('window-all-closed', (event) => {
  event.preventDefault();
  if (mainWindow) {
    mainWindow.hide();
  }
});

app.on('before-quit', () => {
  globalShortcut.unregisterAll();
  if (serverProcess && process.env.DAVE_STOP_SERVER_ON_QUIT === '1') {
    serverProcess.kill();
  }
});
