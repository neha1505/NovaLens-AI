const { spawn } = require('child_process');
const path = require('path');

const isWindows = process.platform === 'win32';

console.log('\x1b[36m%s\x1b[0m', '🚀 Launching NovaLens AI Full-Stack Application...\n');

// 1. Spawn FastAPI Backend Server
const backendCmd = isWindows ? 'cmd.exe' : 'python';
const backendArgs = isWindows 
  ? ['/c', 'python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000'] 
  : ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8000'];

const backendProcess = spawn(backendCmd, backendArgs, {
  cwd: process.cwd(),
  stdio: 'pipe'
});

backendProcess.stdout.on('data', (data) => {
  process.stdout.write(`\x1b[35m[Backend]\x1b[0m ${data}`);
});

backendProcess.stderr.on('data', (data) => {
  process.stderr.write(`\x1b[35m[Backend]\x1b[0m ${data}`);
});

// 2. Spawn React Vite Frontend Dev Server
const frontendCmd = isWindows ? 'cmd.exe' : 'npm';
const frontendArgs = isWindows 
  ? ['/c', 'npm run dev'] 
  : ['run', 'dev'];

const frontendProcess = spawn(frontendCmd, frontendArgs, {
  cwd: path.join(process.cwd(), 'frontend'),
  stdio: 'pipe'
});

frontendProcess.stdout.on('data', (data) => {
  process.stdout.write(`\x1b[36m[Frontend]\x1b[0m ${data}`);
});

frontendProcess.stderr.on('data', (data) => {
  process.stderr.write(`\x1b[36m[Frontend]\x1b[0m ${data}`);
});

// Graceful cleanup on exit
let shuttingDown = false;
const cleanExit = () => {
  if (shuttingDown) return;
  shuttingDown = true;
  console.log('\n\x1b[33m%s\x1b[0m', 'Shutting down NovaLens AI backend and frontend servers...');
  try {
    if (backendProcess && !backendProcess.killed) {
      if (isWindows) {
        spawn('taskkill', ['/pid', backendProcess.pid, '/f', '/t']);
      } else {
        backendProcess.kill('SIGINT');
      }
    }
    if (frontendProcess && !frontendProcess.killed) {
      if (isWindows) {
        spawn('taskkill', ['/pid', frontendProcess.pid, '/f', '/t']);
      } else {
        frontendProcess.kill('SIGINT');
      }
    }
  } catch (e) {
    // Ignore cleanup errors
  }
  process.exit(0);
};

process.on('SIGINT', cleanExit);
process.on('SIGTERM', cleanExit);
