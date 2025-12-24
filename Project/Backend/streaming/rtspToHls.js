import { spawn } from 'child_process';
import path from 'path';

export function startRtspToHls(name, rtspUrl, outputRoot) {
  const outputDir = path.join(outputRoot, name);
  const playlistPath = path.join(outputDir, 'index.m3u8');

  const args = [
    '-i', rtspUrl,
    '-rtsp_transport', 'tcp',
    '-fflags', 'nobuffer',
    '-flags', 'low_delay',
    '-an',
    '-c:v', 'copy',
    '-f', 'hls',
    '-hls_time', '2',
    '-hls_list_size', '6',
    '-hls_flags', 'delete_segments+append_list+omit_endlist',
    playlistPath,
  ];

  const ff = spawn('ffmpeg', args, { stdio: 'ignore' });

  ff.on('exit', (code) => {
    console.error(`ffmpeg exited for ${name} with code ${code}`);
  });

  ff.on('error', (err) => {
    console.error(`ffmpeg error for ${name}:`, err);
  });

  return { process: ff, playlistPath };
}

