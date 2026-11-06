import { useEffect, useRef, useState } from "react";

type LocationCaptureProps = {
  tripId: number;
  accessToken: string;
};

export default function LocationCapture({
  tripId,
  accessToken,
}: LocationCaptureProps) {
  const [running, setRunning] = useState(false);
  const [savedCount, setSavedCount] = useState(0);
  const [accuracy, setAccuracy] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const watchRef = useRef<number | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const generationRef = useRef(0);

  useEffect(() => {
    return () => {
      generationRef.current += 1;

      if (watchRef.current !== null) {
        navigator.geolocation.clearWatch(watchRef.current);
        watchRef.current = null;
      }

      controllerRef.current?.abort();
    };
  }, [tripId, accessToken]);

  function stopCollection() {
    generationRef.current += 1;

    if (watchRef.current !== null) {
      navigator.geolocation.clearWatch(watchRef.current);
      watchRef.current = null;
    }

    const hadPendingRequest = controllerRef.current !== null;

    controllerRef.current?.abort();
    controllerRef.current = null;

    setRunning(false);
    setMessage(
      hadPendingRequest
        ? "Coleta parada. Havia um envio em andamento; atualize o percurso para conferir o último registro."
        : "Coleta parada. Os pontos confirmados continuam salvos.",
    );
  }

  function startCollection() {
    if (watchRef.current !== null) return;

    setError("");
    setMessage("");

    if (!window.isSecureContext || !navigator.geolocation) {
      setError(
        "A localização exige um navegador compatível e acesso por HTTPS ou localhost.",
      );
      return;
    }

    const generation = generationRef.current + 1;
    generationRef.current = generation;

    let sending = false;
    let lastSentAt = 0;

    setSavedCount(0);
    setAccuracy(null);
    setRunning(true);
    setMessage("Aguardando localização e permissão do navegador…");

    function stopWithError(description: string) {
      if (generationRef.current !== generation) return;

      generationRef.current += 1;

      if (watchRef.current !== null) {
        navigator.geolocation.clearWatch(watchRef.current);
        watchRef.current = null;
      }

      controllerRef.current?.abort();
      controllerRef.current = null;

      setRunning(false);
      setMessage("");
      setError(description);
    }

    async function sendPosition(position: GeolocationPosition) {
      if (generationRef.current !== generation) return;

      setAccuracy(Math.round(position.coords.accuracy));

      if (sending || Date.now() - lastSentAt < 10000) return;

      sending = true;

      const controller = new AbortController();
      controllerRef.current = controller;

      const timer = window.setTimeout(() => controller.abort(), 15000);

      try {
        const response = await fetch(`/api/trips/${tripId}/locations/`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${accessToken}`,
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          signal: controller.signal,
          body: JSON.stringify({
            point_id: crypto.randomUUID(),
            latitude: Number(position.coords.latitude.toFixed(7)),
            longitude: Number(position.coords.longitude.toFixed(7)),
            accuracy_m: Number(position.coords.accuracy.toFixed(2)),
            recorded_at: new Date(position.timestamp).toISOString(),
          }),
        });

        if (!response.ok) {
          const detail = await response.text();

          throw new Error(
            response.status === 401
              ? "Sessão expirada. Entre novamente antes de retomar a coleta."
              : response.status === 403
                ? "Somente o motorista responsável pode enviar os pontos."
                : `Envio recusado (${response.status}): ${detail}`,
          );
        }

        if (generationRef.current !== generation) return;

        lastSentAt = Date.now();

        setSavedCount((value) => value + 1);
        setMessage(
          "Coleta ativa. O último ponto enviado foi confirmado pelo servidor.",
        );
      } catch (caught: unknown) {
        if (generationRef.current !== generation) return;

        stopWithError(
          caught instanceof Error && caught.name !== "AbortError"
            ? `Coleta interrompida: ${caught.message}`
            : "Coleta interrompida por falha ou demora no envio. Atualize o percurso para verificar o último ponto antes de reiniciar.",
        );
      } finally {
        window.clearTimeout(timer);
        sending = false;

        if (controllerRef.current === controller) {
          controllerRef.current = null;
        }
      }
    }

    watchRef.current = navigator.geolocation.watchPosition(
      (position) => {
        void sendPosition(position);
      },
      (locationError) => {
        stopWithError(
          locationError.code === 1
            ? "Permissão de localização negada. Autorize nas configurações do navegador."
            : locationError.code === 2
              ? "Localização indisponível. Confira as configurações do dispositivo e tente novamente."
              : "O navegador demorou para obter a localização. Tente iniciar novamente.",
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
          onClick={running ? stopCollection : startCollection}
        >
          {running ? "Parar coleta" : "Iniciar coleta"}
        </button>
      </div>

      <dl className="trip-information">
        <div>
          <dt>Estado</dt>
          <dd>{running ? "Ativa" : "Parada"}</dd>
        </div>

        <div>
          <dt>Pontos confirmados nesta sessão de coleta</dt>
          <dd>{savedCount}</dd>
        </div>

        <div>
          <dt>Precisão da última posição recebida</dt>
          <dd>
            {accuracy === null ? "Aguardando localização" : `${accuracy} m`}
          </dd>
        </div>
      </dl>

      {message && <p role="status">{message}</p>}

      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      <p className="trip-map-note">
        Mantenha esta página aberta e em primeiro plano. Trocar de viagem, sair
        da conta ou fechar a página encerra a coleta. Parar a coleta não
        finaliza a viagem.
      </p>

      <p className="trip-map-note">
        Esta versão não possui fila de envio offline. Atualize o percurso para
        consultar os pontos salvos.
      </p>
    </section>
  );
}
