import { useEffect, useState } from "react";
import "./TripsPanel.css";
import TripPhotos from "./TripPhotos";
import TripMap from "./TripMap";
import LocationCapture from "./LocationCapture";

type Trip = {
  id: number;
  driver: number;
  driver_username: string;
  vehicle: number;
  vehicle_plate: string;
  origin: string;
  destination: string;
  notes: string;
  status: string;
  start_km: number | null;
  end_km: number | null;
  started_at: string | null;
  ended_at: string | null;
  traveled_km: number | null;
  created_at: string;
  updated_at: string;
};

type PaginatedTrips = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Trip[];
};

type ResourceState<T> = {
  key: string;
  data: T | null;
  error: string;
};

type TripsPanelProps = {
  accessToken: string;
};

const statusNames: Record<string, string> = {
  PLANNED: "Planejada",
  IN_PROGRESS: "Em andamento",
  COMPLETED: "Finalizada",
  CANCELLED: "Cancelada",
};

function formatDate(value: string | null | undefined): string {
  if (!value) return "Não registrado";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "Data indisponível";

  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function formatKm(value: number | null | undefined): string {
  if (value == null) return "Não informado";

  return `${value.toLocaleString("pt-BR")} km`;
}

function useApiResource<T>(
  url: string | null,
  accessToken: string,
  revision: number,
) {
  const key = JSON.stringify([url, accessToken, revision]);

  const [state, setState] = useState<ResourceState<T>>({
    key: "",
    data: null,
    error: "",
  });

  useEffect(() => {
    if (!url) return;

    const controller = new AbortController();

    let cancelled = false;
    let timedOut = false;

    const timer = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 15000);

    fetch(url, {
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          const message =
            response.status === 401
              ? "Sua sessão expirou. Saia e entre novamente."
              : response.status === 403
                ? "Sua conta não permite esta consulta."
                : response.status === 404
                  ? "A viagem não foi encontrada ou não está disponível para sua conta."
                  : "Não foi possível carregar as informações.";

          throw new Error(message);
        }

        return (await response.json()) as T;
      })
      .then((data) => {
        if (cancelled) return;

        setState({
          key,
          data,
          error: "",
        });
      })
      .catch((caught: unknown) => {
        if (cancelled) return;

        const message = timedOut
          ? "O serviço demorou para responder. Tente atualizar."
          : caught instanceof TypeError
            ? "Não foi possível conectar ao serviço. Tente novamente."
            : caught instanceof SyntaxError
              ? "O serviço retornou uma resposta inválida."
              : caught instanceof Error
                ? caught.message
                : "Não foi possível carregar as informações.";

        setState({
          key,
          data: null,
          error: message,
        });
      })
      .finally(() => {
        window.clearTimeout(timer);
      });

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [url, accessToken, key]);

  const current = state.key === key;

  return {
    data: current ? state.data : null,
    error: current ? state.error : "",
    loading: url !== null && !current,
  };
}

function TripDetails({
  trip,
  accessToken,
}: {
  trip: Trip;
  accessToken: string;
}) {
  return (
    <article className="trip-details">
      <div className="trip-details-heading">
        <div>
          <span className="trip-eyebrow">Detalhes da viagem</span>
          <h4>Viagem #{trip.id}</h4>
        </div>

        <span className="trip-status">
          {statusNames[trip.status] ?? trip.status}
        </span>
      </div>

      <div className="trip-route">
        <div>
          <span className="route-dot route-dot-start" />
          <div>
            <span className="trip-eyebrow">Origem</span>
            <strong>{trip.origin}</strong>
          </div>
        </div>

        <div>
          <span className="route-dot route-dot-end" />
          <div>
            <span className="trip-eyebrow">Destino</span>
            <strong>{trip.destination}</strong>
          </div>
        </div>
      </div>

      <dl className="trip-information">
        <div>
          <dt>Motorista</dt>
          <dd>{trip.driver_username}</dd>
        </div>

        <div>
          <dt>Veículo</dt>
          <dd>{trip.vehicle_plate}</dd>
        </div>

        <div>
          <dt>Quilometragem inicial</dt>
          <dd>{formatKm(trip.start_km)}</dd>
        </div>

        <div>
          <dt>Quilometragem final</dt>
          <dd>{formatKm(trip.end_km)}</dd>
        </div>

        <div>
          <dt>Distância pelo hodômetro</dt>
          <dd>{formatKm(trip.traveled_km)}</dd>
        </div>

        <div>
          <dt>Planejamento registrado</dt>
          <dd>{formatDate(trip.created_at)}</dd>
        </div>

        <div>
          <dt>Início</dt>
          <dd>{formatDate(trip.started_at)}</dd>
        </div>

        <div>
          <dt>Finalização</dt>
          <dd>{formatDate(trip.ended_at)}</dd>
        </div>
      </dl>

      <p className="trip-timezone">Horários de Brasília.</p>

      <TripPhotos key={trip.id} tripId={trip.id} accessToken={accessToken} />
      
            <TripMap
        key={trip.id}
        tripId={trip.id}
        accessToken={accessToken}
      />
      
      {trip.status === "IN_PROGRESS" && (
        <LocationCapture
          key={trip.id}
          tripId={trip.id}
          accessToken={accessToken}
        />
      )}

      {trip.notes && (
        <div className="trip-notes">
          <h5>Observações</h5>
          <p>{trip.notes}</p>
        </div>
      )}
    </article>
  );
}

export default function TripsPanel({ accessToken }: TripsPanelProps) {
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [revision, setRevision] = useState(0);

  const list = useApiResource<PaginatedTrips>(
    `/api/trips/?page=${page}`,
    accessToken,
    revision,
  );

  const detail = useApiResource<Trip>(
    selectedId === null ? null : `/api/trips/${selectedId}/`,
    accessToken,
    revision,
  );

  function changePage(nextPage: number) {
    setPage(nextPage);
    setSelectedId(null);
  }

  return (
    <section className="trips-panel" aria-labelledby="trips-heading">
      <div className="trips-toolbar">
        <div>
          <h3 id="trips-heading">Viagens</h3>
          <p>
            {list.data
              ? `${list.data.count} viagem(ns) disponível(is) para sua conta.`
              : "Consulte os registros das viagens."}
          </p>
        </div>

        <button
          className="trip-button"
          type="button"
          onClick={() => setRevision((value) => value + 1)}
          disabled={list.loading || detail.loading}
        >
          Atualizar
        </button>
      </div>

      <div className="trips-layout">
        <div className="trips-list-area" aria-busy={list.loading}>
          {list.loading && (
            <p className="trip-empty" role="status">
              Carregando viagens…
            </p>
          )}

          {list.error && (
            <div className="error-message" role="alert">
              {list.error}
            </div>
          )}

          {list.data && list.data.results.length === 0 && (
            <p className="trip-empty">
              Nenhuma viagem disponível nesta página.
            </p>
          )}

          {list.data && (
            <>
              <div className="trips-list">
                {list.data.results.map((trip) => (
                  <button
                    key={trip.id}
                    className={`trip-entry ${
                      selectedId === trip.id ? "trip-entry-selected" : ""
                    }`}
                    type="button"
                    onClick={() => setSelectedId(trip.id)}
                    aria-pressed={selectedId === trip.id}
                  >
                    <span className="trip-entry-heading">
                      <strong>Viagem #{trip.id}</strong>
                      <span className="trip-status">
                        {statusNames[trip.status] ?? trip.status}
                      </span>
                    </span>

                    <span className="trip-entry-route">
                      {trip.origin} → {trip.destination}
                    </span>

                    <span className="trip-entry-caption">
                      {trip.vehicle_plate} · {trip.driver_username}
                    </span>
                  </button>
                ))}
              </div>

              <nav className="trips-pagination" aria-label="Páginas de viagens">
                <button
                  className="trip-button"
                  type="button"
                  disabled={!list.data.previous}
                  onClick={() => changePage(Math.max(1, page - 1))}
                >
                  Anterior
                </button>

                <span>Página {page}</span>

                <button
                  className="trip-button"
                  type="button"
                  disabled={!list.data.next}
                  onClick={() => changePage(page + 1)}
                >
                  Próxima
                </button>
              </nav>
            </>
          )}
        </div>

        <div className="trip-detail-area" aria-busy={detail.loading}>
          {selectedId === null && (
            <div className="trip-selection-placeholder">
              <strong>Selecione uma viagem</strong>
              <p>
                Os dados do motorista, do veículo e do deslocamento aparecerão
                aqui.
              </p>
            </div>
          )}

          {detail.loading && (
            <p className="trip-empty" role="status">
              Carregando detalhes…
            </p>
          )}

          {detail.error && (
            <div className="error-message" role="alert">
              {detail.error}
            </div>
          )}

          {detail.data && (
            <TripDetails trip={detail.data} accessToken={accessToken} />
          )}
        </div>
      </div>
    </section>
  );
}
