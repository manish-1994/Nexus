const { spawn, exec } = require('child_process');
const http = require('http');
const path = require('path');

const BACKEND_PORT = 8000;
const FRONTEND_PORT = 5173;
const HEALTH_URL = `http://localhost:${BACKEND_PORT}/api/v1/health/health`;
const HEALTH_TIMEOUT = 60000; // 60 seconds
const HEALTH_POLL_INTERVAL = 1000; // 1 second
const GRACEFUL_SHUTDOWN_TIMEOUT = 3000; // 3 seconds
const PORT_RELEASE_DELAY = 2000; // 2 seconds

// Use npx vite directly to avoid recursive npm run dev
const FRONTEND_CMD = 'npx';
const FRONTEND_ARGS = ['vite'];

let backendProcess = null;
let frontendProcess = null;
let isShuttingDown = false;

function log(prefix, message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] [${prefix}] ${message}`);
}

function findProcessOnPort(port) {
  return new Promise((resolve) => {
    // Use netstat to find process on port (Windows)
    exec(`netstat -ano | findstr :${port}`, (error, stdout) => {
      if (error) {
        resolve(null);
        return;
      }

      const lines = stdout.split('\n');
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.includes('LISTENING')) {
          const parts = trimmed.split(/\s+/);
          const pid = parts[parts.length - 1];
          if (pid && !isNaN(pid)) {
            resolve(pid);
            return;
          }
        }
      }
      resolve(null);
    });
  });
}

async function killProcess(pid, force = false) {
  return new Promise((resolve) => {
    if (!pid) {
      resolve();
      return;
    }

    log('Runner', `Stopping process ${pid}...`);

    if (force) {
      exec(`taskkill /F /PID ${pid}`, (error) => {
        if (error) {
          log('Runner', `Failed to kill process ${pid}: ${error.message}`);
        } else {
          log('Runner', `Process ${pid} terminated`);
        }
        resolve();
      });
    } else {
      // Try graceful shutdown first
      try {
        process.kill(pid, 'SIGTERM');
        log('Runner', `Sent SIGTERM to process ${pid}`);
        setTimeout(() => {
          // Force kill if still running after timeout
          killProcess(pid, true).then(resolve);
        }, GRACEFUL_SHUTDOWN_TIMEOUT);
      } catch (error) {
        log('Runner', `Process ${pid} already stopped or failed to stop gracefully`);
        resolve();
      }
    }
  });
}

async function waitForHealth() {
  log('Runner', 'Waiting for backend health endpoint...');

  return new Promise((resolve, reject) => {
    const startTime = Date.now();

    const checkHealth = () => {
      if (isShuttingDown) {
        reject(new Error('Shutdown requested during health check'));
        return;
      }

      http.get(HEALTH_URL, (res) => {
        if (res.statusCode === 200) {
          log('Runner', 'Backend is healthy');
          resolve();
        } else {
          retry();
        }
      }).on('error', retry);

      function retry() {
        if (Date.now() - startTime > HEALTH_TIMEOUT) {
          reject(new Error('Backend health check timeout'));
          return;
        }
        setTimeout(checkHealth, HEALTH_POLL_INTERVAL);
      }
    };

    checkHealth();
  });
}

function startBackend() {
  return new Promise((resolve, reject) => {
    log('Runner', 'Starting backend server...');

    const backendDir = path.join(__dirname, '..', 'backend');
    backendProcess = spawn('python', ['-m', 'uvicorn', 'app:app', '--host', '0.0.0.0', '--port', String(BACKEND_PORT)], {
      cwd: backendDir,
      stdio: 'pipe',
      shell: true,
    });

    backendProcess.stdout.on('data', (data) => {
      const lines = data.toString().split('\n').filter(line => line.trim());
      for (const line of lines) {
        log('Backend', line);
      }
    });

    backendProcess.stderr.on('data', (data) => {
      const lines = data.toString().split('\n').filter(line => line.trim());
      for (const line of lines) {
        log('Backend', line);
      }
    });

    backendProcess.on('error', (error) => {
      log('Runner', `Backend failed to start: ${error.message}`);
      reject(error);
    });

    backendProcess.on('exit', (code, signal) => {
      if (!isShuttingDown) {
        log('Runner', `Backend exited unexpectedly with code ${code}, signal ${signal}`);
      }
      backendProcess = null;
    });

    // Wait for health check instead of arbitrary timeout
    waitForHealth()
      .then(() => resolve())
      .catch((error) => {
        log('Runner', `Backend startup failed: ${error.message}`);
        reject(error);
      });
  });
}

function startFrontend() {
  return new Promise((resolve, reject) => {
    log('Runner', 'Starting frontend dev server...');

    const frontendDir = path.join(__dirname, '..', 'frontend');
    frontendProcess = spawn(FRONTEND_CMD, FRONTEND_ARGS, {
      cwd: frontendDir,
      stdio: 'pipe',
      shell: true,
    });

    frontendProcess.stdout.on('data', (data) => {
      const lines = data.toString().split('\n').filter(line => line.trim());
      for (const line of lines) {
        log('Frontend', line);
      }
    });

    frontendProcess.stderr.on('data', (data) => {
      const lines = data.toString().split('\n').filter(line => line.trim());
      for (const line of lines) {
        log('Frontend', line);
      }
    });

    frontendProcess.on('error', (error) => {
      log('Runner', `Frontend failed to start: ${error.message}`);
      reject(error);
    });

    frontendProcess.on('exit', (code, signal) => {
      if (!isShuttingDown) {
        log('Runner', `Frontend exited unexpectedly with code ${code}, signal ${signal}`);
      }
      frontendProcess = null;
    });

    // Give frontend a moment to start, then resolve
    // Vite typically starts quickly, we don't need a health check for it
    setTimeout(() => {
      if (frontendProcess && !isShuttingDown) {
        log('Runner', 'Frontend started');
        resolve();
      }
    }, 2000);
  });
}

async function ensurePortsFree() {
  const backendPid = await findProcessOnPort(BACKEND_PORT);
  const frontendPid = await findProcessOnPort(FRONTEND_PORT);

  if (backendPid) {
    log('Runner', `Found backend process on port ${BACKEND_PORT} (PID: ${backendPid})`);
    await killProcess(backendPid);
  }
  if (frontendPid) {
    log('Runner', `Found frontend process on port ${FRONTEND_PORT} (PID: ${frontendPid})`);
    await killProcess(frontendPid);
  }

  if (backendPid || frontendPid) {
    log('Runner', `Waiting for ports to be released...`);
    await new Promise(resolve => setTimeout(resolve, PORT_RELEASE_DELAY));
  }
}

async function cleanup() {
  if (isShuttingDown) {
    return;
  }
  isShuttingDown = true;

  log('Runner', 'Shutting down services...');

  // Stop frontend first
  if (frontendProcess) {
    try {
      frontendProcess.kill('SIGTERM');
      log('Runner', 'Frontend stopped');
    } catch (error) {
      log('Runner', `Error stopping frontend: ${error.message}`);
    }
    frontendProcess = null;
  }

  // Stop backend
  if (backendProcess) {
    try {
      backendProcess.kill('SIGTERM');
      log('Runner', 'Backend stopped');
    } catch (error) {
      log('Runner', `Error stopping backend: ${error.message}`);
    }
    backendProcess = null;
  }

  // Ensure ports are free by killing any remaining processes
  await ensurePortsFree();

  log('Runner', 'Shutdown complete');
}

async function main() {
  log('Runner', 'Starting NEXUS V3 development runner...');

  // Step 1: Ensure ports are free before starting
  log('Runner', 'Checking for existing processes...');
  await ensurePortsFree();

  // Step 2: Start backend
  try {
    await startBackend();
  } catch (error) {
    log('Runner', `Failed to start backend: ${error.message}`);
    await cleanup();
    process.exit(1);
  }

  // Step 4: Start frontend
  try {
    await startFrontend();
  } catch (error) {
    log('Runner', `Failed to start frontend: ${error.message}`);
    await cleanup();
    process.exit(1);
  }

  log('Runner', 'All services started successfully');
  log('Runner', `Backend: http://localhost:${BACKEND_PORT}`);
  log('Runner', `Frontend: http://localhost:${FRONTEND_PORT}`);
  log('Runner', 'Press Ctrl+C to stop all services');
}

// Handle shutdown
process.on('SIGINT', async () => {
  log('Runner', 'Received SIGINT, shutting down...');
  await cleanup();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  log('Runner', 'Received SIGTERM, shutting down...');
  await cleanup();
  process.exit(0);
});

// Handle uncaught errors
process.on('uncaughtException', async (error) => {
  log('Runner', `Uncaught exception: ${error.message}`);
  await cleanup();
  process.exit(1);
});

process.on('unhandledRejection', async (reason) => {
  log('Runner', `Unhandled rejection: ${reason}`);
  await cleanup();
  process.exit(1);
});

// Start the runner
main().catch(async (error) => {
  log('Runner', `Fatal error: ${error.message}`);
  await cleanup();
  process.exit(1);
});
