import { useEffect, useState } from "react";
import "./TripPhotos.css";

type PhotoProps = {
  tripId: number;
  accessToken: string;
  stage: "start" | "end";
  revision: number;
};

type PhotoState = {
  key: string;
  url: string;
  error: string;
};

function OdometerPhoto({ tripId, accessToken, stage, revision }: PhotoProps) {
  const key = JSON.stringify([tripId, accessToken, stage, revision]);

  const [state, setState] = useState<PhotoState>({
    key: "",
    url: "",
    error: "",
  });

  useEffect(() => {
    const controller = new AbortController();

    let cancelled = false;
    let timedOut = false;
    let objectUrl = "";

    const timer = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 15000);

    async function loadPhoto() {
      try {
        const response = await fetch(
          `/api/trips/${tripId}/odometer-photo/${stage}/`,
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
              Accept: "application/json",
            },
            cache: "no-store",
            signal: controller.signal,
          },
        );

        if (!response.ok) {
          const message =
            response.status === 404
              ? "Foto não disponível."
              : response.status === 401
                ? "Sua sessão expirou. Saia e entre novamente."
                : response.status === 403
                  ? "Sua conta não permite consultar esta foto."
                  : "Não foi possível carregar a foto.";

          throw new Error(message);
        }

        const blob = await response.blob();

        if (!["image/jpeg", "image/png"].includes(blob.type)) {
          throw new Error(
            "O serviço retornou um formato de imagem inesperado.",
          );
        }

        if (cancelled) return;

        objectUrl = URL.createObjectURL(blob);

        setState({
          key,
          url: objectUrl,
          error: "",
        });
      } catch (caught: unknown) {
        if (cancelled) return;

        setState({
          key,
          url: "",
          error: timedOut
            ? "A foto demorou para carregar. Tente atualizar."
            : caught instanceof Error
              ? caught.message
              : "Não foi possível carregar a foto.",
        });
      } finally {
        window.clearTimeout(timer);
      }
    }

    void loadPhoto();

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
      controller.abort();

      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [tripId, accessToken, stage, key]);

  const current = state.key === key;
  const title = stage === "start" ? "Hodômetro inicial" : "Hodômetro final";

  return (
    <figure className="odometer-photo">
      <figcaption>{title}</figcaption>

      {!current && (
        <p className="photo-message" role="status">
          Carregando foto…
        </p>
      )}

      {current && state.error && (
        <p className="photo-message" role="status">
          {state.error}
        </p>
      )}

      {current && state.url && (
        <img src={state.url} alt={`${title} da viagem ${tripId}`} />
      )}
    </figure>
  );
}

type TripPhotosProps = {
  tripId: number;
  accessToken: string;
};

export default function TripPhotos({ tripId, accessToken }: TripPhotosProps) {
  const [revision, setRevision] = useState(0);

  return (
    <section className="trip-photos" aria-label="Fotos do hodômetro">
      <div className="trip-photos-heading">
        <h5>Fotos do hodômetro</h5>

        <button
          className="trip-button"
          type="button"
          onClick={() => setRevision((value) => value + 1)}
        >
          Atualizar fotos
        </button>
      </div>

      <div className="trip-photos-grid">
        <OdometerPhoto
          tripId={tripId}
          accessToken={accessToken}
          stage="start"
          revision={revision}
        />

        <OdometerPhoto
          tripId={tripId}
          accessToken={accessToken}
          stage="end"
          revision={revision}
        />
      </div>
    </section>
  );
}
