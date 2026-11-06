import { useCallback, useEffect, useRef, useState } from "react";
import { sendGPSBatch } from "../services/gpsApi";
import type { GPSPoint } from "../services/gpsApi";

type LocationCaptureProps = {
  tripId: number;
  accessToken: string;
};

export default function LocationCapture({
  tripId,
  accessToken,
}: LocationCaptureProps) {
  const [running, setRunning] = useState(false);
  const [sending, setSending] = useState(false);
  const [pending, setPending] = useState(0);
  const [confirmed, setConfirmed] = useState(0);
  const [accuracy, setAccuracy] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const queueRef = useRef<GPSPoint[]>([]);
  const watchRef = useRef<number | null>(null);
  const busyRef = useRef(false);
  const activeRef = useRef(false);
  const automaticRef = useRef(false);
  const lastCapturedRef = useRef(0);

  const flushQueue = useCallback(async () => {
    if (busyRef.current || queueRef.current.length === 0) return;

    const batch = queueRef.current.slice(0, 100);

    busyRef.current = true;
    setSending(true);
    setError("");

    try {
      const result = await sendGPSBatch(tripId, accessToken, batch);

      if (!activeRef.current) return;

      const confirmedIds = new Set(batch.map((point) => point.point_id));

      queueRef.current = queueRef.current.filter(
        (point) => !confirmedIds.has(point.point_id),
      );

      setPending(queueRef.current.length);
      setConfirmed((value) => value + result.received);
      setMessage(
        `Lote confirmado: ${result.created} novos e ${result.existing} já existentes.`,
      );
    } catch (caught: unknown) {
      if (!activeRef.current) return;

      automaticRef.current = false;

      if (watchRef.current !== null) {
        navigator.geolocation.clearWatch(watchRef.current);
        watchRef.current = null;
      }

      setRunning(false);
      setMessage("");
      setError(
        `${
          caught instanceof Error
            ? caught.message
            : "Não foi possível confirmar o lote."
        } A coleta foi parada. Os pontos continuam pendentes nesta página.`,
      );
    } finally {
      busyRef.current = false;

      if (activeRef.current) {
        setSending(false);
      }
    }
  }, [tripId, accessToken]);

  useEffect(() => {
    activeRef.current = true;

    const timer = window.setInterval(() => {
      if (automaticRef.current) {
        void flushQueue();
      }
    }, 15000);

    function warnBeforeLeaving(event: BeforeUnloadEvent) {
      if (queueRef.current.length === 0) return;

      event.preventDefault();
      event.returnValue = "";
    }

    window.addEventListener("beforeunload", warnBeforeLeaving);

    return () => {
      activeRef.current = false;
      automaticRef.current = false;
      window.clearInterval(timer);
      window.removeEventListener("beforeunload", warnBeforeLeaving);

      if (watchRef.current !== null) {
        navigator.geolocation.clearWatch(watchRef.current);
        watchRef.current = null;
      }
    };
  }, [flushQueue]);

  function stopCollection() {
    automaticRef.current = false;

    if (watchRef.current !== null) {
      navigator.geolocation.clearWatch(watchRef.current);
      watchRef.current = null;
    }

    setRunning(false);
    setMessage(
      "Coleta parada. Envie os pontos pendentes antes de sair desta viagem.",
    );
  }

  function startCollection() {
    if (watchRef.current !== null || busyRef.current) return;

    setError("");

    if (!window.isSecureContext || !navigator.geolocation) {
      setError(
        "A localização exige HTTPS ou localhost e um navegador compatível.",
      );
      return;
    }

    if (queueRef.current.length >= 1000) {
      setError(
        "A fila atingiu 1.000 pontos. Envie os pendentes antes de continuar.",
      );
      return;
    }

    lastCapturedRef.current = 0;
    automaticRef.current = true;
    setRunning(true);
    setMessage("Aguardando localização…");

    watchRef.current = navigator.geolocation.watchPosition(
      (position) => {
        if (!activeRef.current || !automaticRef.current) return;

        setAccuracy(Math.round(position.coords.accuracy));

        if (Date.now() - lastCapturedRef.current < 10000) {
          return;
        }

        if (queueRef.current.length >= 1000) {
          stopCollection();
          setError(
            "A fila atingiu 1.000 pontos. Envie os pendentes para continuar.",
          );
          return;
        }

        const point: GPSPoint = {
          point_id: crypto.randomUUID(),
          latitude: Number(position.coords.latitude.toFixed(7)),
          longitude: Number(position.coords.longitude.toFixed(7)),
          accuracy_m: Number(position.coords.accuracy.toFixed(2)),
          recorded_at: new Date(position.timestamp).toISOString(),
        };

        queueRef.current.push(point);
        lastCapturedRef.current = Date.now();

        setPending(queueRef.current.length);
        setMessage(
          "Coleta ativa. Os pontos aguardam confirmação do envio em lote.",
        );
      },
      (locationError) => {
        if (!activeRef.current || !automaticRef.current) return;

        stopCollection();

        setError(
          locationError.code === 1
            ? "Permissão de localização negada."
            : locationError.code === 2
              ? "O dispositivo não conseguiu determinar a localização."
              : "O navegador demorou para obter uma posição. Tente iniciar novamente.",
        );
      },
      {
        enableHighAccuracy: true,
        timeout: 20000,
        maximumAge: 0,
      },
    );
  }

  return (
    <section className="trip-map-section" aria-label="Coleta de localização">
      <div className="trip-map-heading">
        <h5>Coleta de localização</h5>

        <button
          className="trip-button"
          type="button"
          disabled={!running && sending}
          onClick={running ? stopCollection : startCollection}
        >
          {running ? "Parar coleta" : "Iniciar coleta"}
        </button>

        <button
          className="trip-button"
          type="button"
          disabled={sending || pending === 0}
          onClick={() => void flushQueue()}
        >
          {sending ? "Enviando…" : "Enviar pendentes"}
        </button>
      </div>

      <dl className="trip-information">
        <div>
          <dt>Estado da coleta</dt>
          <dd>{running ? "Ativa" : "Parada"}</dd>
        </div>

        <div>
          <dt>Pontos pendentes</dt>
          <dd>{pending}</dd>
        </div>

        <div>
          <dt>Pontos confirmados nesta tela</dt>
          <dd>{confirmed}</dd>
        </div>

        <div>
          <dt>Precisão da última posição</dt>
          <dd>{accuracy === null ? "Aguardando" : `${accuracy} m`}</dd>
        </div>
      </dl>

      {message && <p role="status">{message}</p>}

      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      <p className="trip-map-note">
        Mantenha a página aberta e em primeiro plano. A coleta aceita uma
        posição a cada 10 segundos e tenta enviar os pendentes a cada 15
        segundos.
      </p>

      <p className="trip-map-note">
        A fila existe somente na memória. Antes de trocar de viagem, sair da
        conta ou fechar a página, pare a coleta e envie todos os pendentes.
        Ainda não há armazenamento offline persistente.
      </p>
    </section>
  );
}
