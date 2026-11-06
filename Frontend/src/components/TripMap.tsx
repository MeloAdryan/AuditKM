import { useEffect, useRef, useState } from "react";
import * as L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./TripMap.css";

type LocationPoint = {
  id: number;
  latitude: string | number;
  longitude: string | number;
  accuracy_m: string | number | null;
  recorded_at: string;
};

type LocationPage = {
  next: string | null;
  previous: string | null;
  results: LocationPoint[];
};

type MapState = {
  key: string;
  points: LocationPoint[];
  error: string;
};

type TripMapProps = {
  tripId: number;
  accessToken: string;
};

function formatTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Horário indisponível";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    dateStyle: "short",
    timeStyle: "medium",
  }).format(date);
}

function RouteCanvas({ points }: { points: LocationPoint[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || points.length === 0) return;

    const coordinates: L.LatLngTuple[] = points.map((point) => [
      Number(point.latitude),
      Number(point.longitude),
    ]);

    const map = L.map(containerRef.current, {
      scrollWheelZoom: false,
    });

    L.tileLayer(
      "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        maxZoom: 19,
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      },
    ).addTo(map);

    if (coordinates.length > 1) {
      L.polyline(coordinates, {
        color: "#078b83",
        weight: 4,
        opacity: 0.9,
      }).addTo(map);
    }

        const lastPoint = points[points.length - 1];

    const lastAccuracy =
      lastPoint.accuracy_m === null
        ? null
        : Number(lastPoint.accuracy_m);

    if (
      lastAccuracy !== null &&
      Number.isFinite(lastAccuracy) &&
      lastAccuracy > 0
    ) {
      L.circle(coordinates[coordinates.length - 1], {
        radius: lastAccuracy,
        color: "#102c4c",
        weight: 1,
        fillColor: "#102c4c",
        fillOpacity: 0.08,
        interactive: false,
      }).addTo(map);
    }

    L.circleMarker(coordinates[0], {
      radius: 8,
      color: "#ffffff",
      weight: 2,
      fillColor: "#078b83",
      fillOpacity: 1,
    })
      .addTo(map)
      .bindTooltip("Primeiro ponto registrado");

    if (coordinates.length > 1) {
      L.circleMarker(coordinates[coordinates.length - 1], {
        radius: 8,
        color: "#ffffff",
        weight: 2,
        fillColor: "#102c4c",
        fillOpacity: 1,
      })
        .addTo(map)
        .bindTooltip("Último ponto registrado");

      map.fitBounds(L.latLngBounds(coordinates), {
        padding: [30, 30],
        maxZoom: 16,
      });
    } else {
      map.setView(coordinates[0], 16);
    }

    const observer = new ResizeObserver(() => {
      map.invalidateSize();
    });

    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      map.remove();
    };
  }, [points]);

  return (
    <div
      ref={containerRef}
      className="trip-map-canvas"
      role="region"
      aria-label="Mapa dos pontos GPS registrados na viagem"
    />
  );
}

export default function TripMap({
  tripId,
  accessToken,
}: TripMapProps) {
  const [revision, setRevision] = useState(0);

  const key = JSON.stringify([tripId, accessToken, revision]);

  const [state, setState] = useState<MapState>({
    key: "",
    points: [],
    error: "",
  });

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;
    let timedOut = false;

    const timer = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 60000);

        async function loadPoints() {
      try {
        const points: LocationPoint[] = [];
        const receivedIds = new Set<number>();
        const visitedPages = new Set<string>();

        const endpoint = `/api/trips/${tripId}/track/`;

        let nextUrl: string | null = endpoint;
        let pages = 0;

        while (nextUrl !== null) {
          if (visitedPages.has(nextUrl)) {
            throw new Error(
              "O serviço retornou uma sequência de páginas repetida.",
            );
          }

          visitedPages.add(nextUrl);
          pages += 1;

          if (pages > 200) {
            throw new Error(
              "O percurso ultrapassa o limite desta visualização. Nenhum trajeto parcial será apresentado.",
            );
          }

          const response = await fetch(nextUrl, {
            headers: {
              Accept: "application/json",
              Authorization: `Bearer ${accessToken}`,
            },
            cache: "no-store",
            signal: controller.signal,
          });

          if (!response.ok) {
            throw new Error(
              response.status === 401
                ? "Sua sessão expirou. Saia e entre novamente."
                : response.status === 403
                  ? "Sua conta não permite consultar este percurso."
                  : response.status === 404
                    ? "O percurso não está disponível para sua conta."
                    : "Não foi possível consultar o percurso.",
            );
          }

          const data = (await response.json()) as LocationPage;

          if (
            !Array.isArray(data.results) ||
            (data.next !== null &&
              typeof data.next !== "string")
          ) {
            throw new Error(
              "O serviço retornou uma página de percurso inválida.",
            );
          }

          for (const point of data.results) {
            const latitude = Number(point.latitude);
            const longitude = Number(point.longitude);

            if (
              !Number.isInteger(point.id) ||
              !Number.isFinite(latitude) ||
              !Number.isFinite(longitude) ||
              latitude < -90 ||
              latitude > 90 ||
              longitude < -180 ||
              longitude > 180
            ) {
              throw new Error(
                "O percurso contém um ponto inválido.",
              );
            }

            if (receivedIds.has(point.id)) {
              throw new Error(
                "O percurso mudou durante a consulta ou contém registros repetidos. Tente atualizar.",
              );
            }

            receivedIds.add(point.id);
            points.push(point);
          }

          if (data.next === null) {
            nextUrl = null;
          } else {
            const address = new URL(
              data.next,
              window.location.origin,
            );

            if (address.pathname !== endpoint) {
              throw new Error(
                "O serviço retornou um endereço de percurso inesperado.",
              );
            }

            const cursor = address.searchParams.get("cursor");

            if (!cursor) {
              throw new Error(
                "O serviço retornou uma continuação sem cursor.",
              );
            }

            const parameters = new URLSearchParams({
              cursor,
            });

            nextUrl = `${endpoint}?${parameters.toString()}`;
          }
        }

        if (cancelled) return;

        setState({
          key,
          points,
          error: "",
        });
      } catch (caught: unknown) {
        if (cancelled) return;

        setState({
          key,
          points: [],
          error: timedOut
            ? "O percurso demorou para carregar. Tente atualizar."
            : caught instanceof TypeError
              ? "Não foi possível conectar ao serviço ou interpretar a resposta."
              : caught instanceof Error
                ? caught.message
                : "Não foi possível carregar o percurso.",
        });
      } finally {
        window.clearTimeout(timer);
      }
    }

    void loadPoints();

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [tripId, accessToken, key]);

  const current = state.key === key;
  const loading = !current;
  const first = state.points[0];
  const last = state.points[state.points.length - 1];

  return (
    <section className="trip-map-section" aria-label="Percurso GPS">
      <div className="trip-map-heading">
        <h5>Percurso registrado</h5>

        <button
          className="trip-button"
          type="button"
          disabled={loading}
          onClick={() => setRevision((value) => value + 1)}
        >
          Atualizar percurso
        </button>
      </div>

      {loading && (
        <p role="status">Carregando pontos GPS…</p>
      )}

      {current && state.error && (
        <div className="error-message" role="alert">
          {state.error}
        </div>
      )}

      {current && !state.error && state.points.length === 0 && (
        <p className="trip-map-note">
          Esta viagem ainda não possui pontos GPS registrados.
        </p>
      )}

      {current && !state.error && first && last && (
        <>
          <RouteCanvas points={state.points} />

          <div className="trip-map-legend">
            <span>
              <i className="map-dot map-dot-start" />
              Primeiro ponto
            </span>

            <span>
              <i className="map-dot map-dot-last" />
              Último ponto
            </span>
          </div>

          <dl className="trip-information">
            <div>
              <dt>Pontos registrados</dt>
              <dd>{state.points.length.toLocaleString("pt-BR")}</dd>
            </div>

            <div>
              <dt>Primeiro registro GPS</dt>
              <dd>{formatTime(first.recorded_at)}</dd>
            </div>

            <div>
              <dt>Último registro GPS</dt>
              <dd>{formatTime(last.recorded_at)}</dd>
            </div>

            <div>
              <dt>Precisão do último ponto</dt>
              <dd>
                {last.accuracy_m == null
                  ? "Não informada"
                  : `${Number(last.accuracy_m).toLocaleString("pt-BR")} m`}
              </dd>
            </div>
          </dl>

          <p className="trip-map-note">
            As linhas ligam os pontos GPS registrados e não
            comprovam o caminho entre eles. Horários de Brasília.
          </p>
        </>
      )}
    </section>
  );
}