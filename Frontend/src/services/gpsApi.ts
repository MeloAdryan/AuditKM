export type GPSPoint = {
  point_id: string;
  latitude: number;
  longitude: number;
  accuracy_m: number;
  recorded_at: string;
};

export type GPSBatchResult = {
  received: number;
  created: number;
  existing: number;
  results: {
  point_id: string;
  }[];
};

export async function sendGPSBatch(
  tripId: number,
  accessToken: string,
  points: GPSPoint[],
): Promise<GPSBatchResult> {
  if (points.length === 0 || points.length > 100) {
    throw new Error("O lote deve conter entre 1 e 100 pontos.");
  }

  const identifiers = new Set(points.map((point) => point.point_id));

  if (identifiers.size !== points.length) {
    throw new Error("O lote contém identificadores repetidos.");
  }

  const controller = new AbortController();

  const timer = window.setTimeout(() => controller.abort(), 20000);

  try {
    const response = await fetch(`/api/trips/${tripId}/locations/batch/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      signal: controller.signal,
      body: JSON.stringify({ points }),
    });

    if (!response.ok) {
      throw new Error(
        response.status === 401
          ? "Sessão expirada. Entre novamente para enviar os pontos."
          : response.status === 403
            ? "Sua conta não permite enviar pontos para esta viagem."
            : response.status === 400
              ? "O servidor recusou os dados do lote."
              : `Não foi possível confirmar o lote (${response.status}).`,
      );
    }

    const result = (await response.json()) as GPSBatchResult;

    if (
      result.received !== points.length ||
      !Number.isInteger(result.created) ||
      !Number.isInteger(result.existing) ||
      result.created < 0 ||
      result.existing < 0 ||
      result.created + result.existing !== points.length ||
      !Array.isArray(result.results) ||
      result.results.length !== points.length
    ) {
      throw new Error("O servidor retornou uma confirmação de lote inválida.");
    }

    const confirmed = new Set(result.results.map((point) => point.point_id));

    if (
      confirmed.size !== identifiers.size ||
      [...identifiers].some((id) => !confirmed.has(id))
    ) {
      throw new Error("A confirmação não corresponde aos pontos enviados.");
    }

    return result;
  } catch (caught: unknown) {
    if (caught instanceof Error && caught.name === "AbortError") {
      throw new Error(
        "O envio demorou para responder. O lote pode ter sido recebido; preserve os identificadores para reenviar com segurança.",
        { cause: caught },
      );
    }

    throw caught;
  } finally {
    window.clearTimeout(timer);
  }
}
