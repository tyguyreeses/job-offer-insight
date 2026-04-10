export interface AudioRecorderController {
  start: () => Promise<void>;
  stop: () => Promise<Blob>;
}

export async function createBrowserAudioRecorder(): Promise<AudioRecorderController> {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("This browser does not support audio recording.");
  }
  if (typeof MediaRecorder === "undefined") {
    throw new Error("MediaRecorder is not available in this browser.");
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const recorder = new MediaRecorder(stream);
  const chunks: BlobPart[] = [];

  recorder.addEventListener("dataavailable", (event: BlobEvent) => {
    if (event.data.size > 0) {
      chunks.push(event.data);
    }
  });

  const stop = (): Promise<Blob> =>
    new Promise((resolve, reject) => {
      recorder.addEventListener(
        "stop",
        () => {
          const mimeType = recorder.mimeType || "audio/webm";
          const audioBlob = new Blob(chunks, { type: mimeType });
          for (const track of stream.getTracks()) {
            track.stop();
          }
          resolve(audioBlob);
        },
        { once: true }
      );
      recorder.addEventListener(
        "error",
        () => {
          for (const track of stream.getTracks()) {
            track.stop();
          }
          reject(new Error("Recording failed."));
        },
        { once: true }
      );
      recorder.stop();
    });

  return {
    start: async () => {
      recorder.start();
    },
    stop,
  };
}
