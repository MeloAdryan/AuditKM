import { useState } from "react";
import type { FormEvent } from "react";
import "./App.css";

type Tokens = {
  access: string;
  refresh: string;
};

type AuditUser = {
  id: number;
  username: string;
  first_name: string;
  role: string;
  is_superuser: boolean;
};

type Session = {
  tokens: Tokens;
  user: AuditUser;
};

type IconName = "user" | "lock" | "eye" | "eyeOff" | "arrow" | "fingerprint";

const rememberedUserKey = "auditkm.remembered-user";

const iconPaths: Record<IconName, string> = {
  user: "M20 21a8 8 0 0 0-16 0M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
  lock: "M6 10h12a2 2 0 0 1 2 2v8H4v-8a2 2 0 0 1 2-2ZM8 10V6a4 4 0 0 1 8 0v4",
  eye: "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Zm13 0a3 3 0 1 1-6 0 3 3 0 0 1 6 0",
  eyeOff:
    "M3 3l18 18M10 5a12 12 0 0 1 2 0c6.5 0 10 7 10 7a18 18 0 0 1-3 4M6 6a20 20 0 0 0-4 6s3.5 7 10 7a12 12 0 0 0 5-1M10 10a3 3 0 0 0 4 4",
  arrow: "M5 12h14M13 6l6 6-6 6",
  fingerprint:
    "M4 10a8 8 0 0 1 16 0M7 11a5 5 0 0 1 10 0c0 4-.5 7-2 10M10 12a2 2 0 0 1 4 0c0 4-.5 6-1 8M4 14c0 3 1 5 2 7M7 14c0 2 .5 4 1 5M10 15c0 3 0 4-1 6",
};

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 15000);

  try {
    const headers = new Headers(options.headers);
    headers.set("Content-Type", "application/json");

    const response = await fetch(`/api${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    });

    if (!response.ok) {
      const message =
        response.status === 401
          ? "Usuário ou senha inválidos, ou sessão expirada."
          : response.status === 429
            ? "Muitas tentativas. Aguarde um pouco e tente novamente."
            : response.status === 403
              ? "Sua conta não tem permissão para esta operação."
              : "Não foi possível concluir a solicitação. Tente novamente.";

      throw new ApiError(response.status, message);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    throw new Error(
      "Não foi possível conectar ao serviço. Confira a conexão e tente novamente.",
      { cause: error },
    );
  } finally {
    window.clearTimeout(timer);
  }
}

function readRememberedUser(): string {
  try {
    return localStorage.getItem(rememberedUserKey) ?? "";
  } catch {
    return "";
  }
}

function saveRememberedUser(username: string, remember: boolean) {
  try {
    if (remember) {
      localStorage.setItem(rememberedUserKey, username);
    } else {
      localStorage.removeItem(rememberedUserKey);
    }
  } catch {
    return;
  }
}

function Icon({ name }: { name: IconName }) {
  return (
    <svg
      className="icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={iconPaths[name]} />
    </svg>
  );
}

function BrandMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 100 100" aria-hidden="true">
      <rect width="100" height="100" rx="25" fill="#173657" />

      <path
        d="M60 14C44 14 33 25 33 40c0 14 15 28 27 37 12-9 27-23 27-37 0-15-11-26-27-26Z"
        fill="#23cdbd"
      />

      <path
        d="m49 40 9 9 15-18"
        fill="none"
        stroke="#102c4c"
        strokeWidth="6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <g fill="#fff">
        <circle cx="20" cy="84" r="4.5" />
        <circle cx="33" cy="81" r="2.7" />
        <circle cx="44" cy="76" r="2.5" />
        <circle cx="53" cy="69" r="2.3" />
      </g>
    </svg>
  );
}

export default function App() {
  const [username, setUsername] = useState(readRememberedUser);
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(() => Boolean(readRememberedUser()));
  const [session, setSession] = useState<Session | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (busy) return;

    setError("");

    const cleanUsername = username.trim();

    if (!cleanUsername || !password) {
      setError("Preencha o usuário e a senha.");
      return;
    }

    setBusy(true);

    try {
      const tokens = await apiRequest<Tokens>("/auth/login/", {
        method: "POST",
        body: JSON.stringify({
          username: cleanUsername,
          password,
        }),
      });

      const user = await apiRequest<AuditUser>("/auth/me/", {
        headers: {
          Authorization: `Bearer ${tokens.access}`,
        },
      });

      saveRememberedUser(cleanUsername, remember);
      setSession({ tokens, user });
      setPassword("");
      setShowPassword(false);
    } catch (loginError) {
      setError(
        loginError instanceof Error
          ? loginError.message
          : "Não foi possível entrar.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleLogout() {
    if (!session || busy) return;

    setBusy(true);
    setError("");

    let tokens = session.tokens;

    try {
      try {
        await apiRequest("/auth/logout/", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${tokens.access}`,
          },
          body: JSON.stringify({
            refresh: tokens.refresh,
          }),
        });
      } catch (logoutError) {
        if (!(logoutError instanceof ApiError) || logoutError.status !== 401) {
          throw logoutError;
        }

        tokens = await apiRequest<Tokens>("/auth/refresh/", {
          method: "POST",
          body: JSON.stringify({
            refresh: tokens.refresh,
          }),
        });

        await apiRequest("/auth/logout/", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${tokens.access}`,
          },
          body: JSON.stringify({
            refresh: tokens.refresh,
          }),
        });
      }
    } catch {
      setError(
        "Você saiu deste navegador, mas não foi possível confirmar o encerramento no servidor.",
      );
    } finally {
      setSession(null);
      setPassword("");
      setBusy(false);
    }
  }

  const roleNames: Record<string, string> = {
    ADMIN: "Administrador",
    MANAGER: "Gestor",
    DRIVER: "Motorista",
  };

  return (
    <main className="auth-page">
      <svg
        className="route-decoration"
        viewBox="0 0 1000 260"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <path
          d="M-20 180C150 65 290 270 490 165S790-20 1020 90"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeDasharray="2 13"
          strokeLinecap="round"
        />

        <circle cx="846" cy="39" r="6" fill="currentColor" />
      </svg>

      <header className="auth-header">
        <BrandMark />

        <h1>
          Audit<span>Km</span>
        </h1>

        <p>Controle, rastreamento e auditoria de deslocamentos</p>
      </header>

      <section
        className="login-card"
        aria-labelledby="login-heading"
        aria-busy={busy}
      >
        {session ? (
          <div className="welcome-panel">
            <span className="success-badge">Acesso confirmado</span>

            <h2 id="login-heading">
              Olá, {session.user.first_name || session.user.username}
            </h2>

            <p className="card-description">Login realizado com sucesso.</p>

            <dl className="account-details">
              <div>
                <dt>Usuário</dt>
                <dd>{session.user.username}</dd>
              </div>

              <div>
                <dt>Perfil</dt>
                <dd>{roleNames[session.user.role] ?? session.user.role}</dd>
              </div>
            </dl>

            <button
              className="primary-button"
              type="button"
              onClick={handleLogout}
              disabled={busy}
            >
              {busy ? "Saindo…" : "Sair"}
            </button>
          </div>
        ) : (
          <>
            <h2 id="login-heading">Bem-vindo de volta</h2>

            <p className="card-description">
              Entre com suas credenciais para continuar.
            </p>

            {error && (
              <div className="error-message" role="alert">
                {error}
              </div>
            )}

            <form onSubmit={handleLogin} noValidate>
              <div className="form-field">
                <label htmlFor="username">Usuário</label>

                <div className="input-wrapper">
                  <Icon name="user" />

                  <input
                    id="username"
                    name="username"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    placeholder="Digite seu usuário"
                    autoComplete="username"
                    autoCapitalize="none"
                    spellCheck={false}
                    disabled={busy}
                    required
                  />
                </div>
              </div>

              <div className="form-field">
                <label htmlFor="password">Senha</label>

                <div className="input-wrapper">
                  <Icon name="lock" />

                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Digite sua senha"
                    autoComplete="current-password"
                    disabled={busy}
                    required
                  />

                  <button
                    className="password-toggle"
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={
                      showPassword ? "Ocultar senha" : "Mostrar senha"
                    }
                    aria-pressed={showPassword}
                    disabled={busy}
                  >
                    <Icon name={showPassword ? "eyeOff" : "eye"} />
                  </button>
                </div>
              </div>

              <div className="form-options">
                <label className="remember-option">
                  <input
                    type="checkbox"
                    checked={remember}
                    onChange={(event) => setRemember(event.target.checked)}
                    disabled={busy}
                  />

                  <span>Lembrar meu usuário</span>
                </label>

                <button
                  className="recovery-button"
                  type="button"
                  disabled
                  title="Recuperação de senha ainda indisponível"
                >
                  Esqueci minha senha
                </button>
              </div>

              <button
                className="primary-button"
                type="submit"
                disabled={busy}
              >
                {busy ? (
                  <>
                    <span className="spinner" aria-hidden="true" />
                    Entrando…
                  </>
                ) : (
                  <>
                    Entrar
                    <Icon name="arrow" />
                  </>
                )}
              </button>

              <button
                className="biometric-button"
                type="button"
                disabled
                title="Autenticação biométrica ainda indisponível"
              >
                <Icon name="fingerprint" />
                Entrar com biometria
              </button>
            </form>
          </>
        )}
      </section>

      <footer className="auth-footer">
        AuditKm · Gestão inteligente de frota
      </footer>
    </main>
  );
}