const TRANSLATIONS = {
  en: {
    "lang.toggle": "FR",
    "app.brand": "PULSE",
    "auth.login.title": "Sign in",
    "auth.login.subtitle": "Sign in to continue to your campus wellness feed",
    "auth.login.email": "Email",
    "auth.login.password": "Password",
    "auth.login.remember": "Remember me",
    "auth.login.forgot": "Forgot password?",
    "auth.login.submit": "Login",
    "auth.login.no_account": "No account?",
    "auth.login.create": "Create one",
    "auth.register.title": "Create your account",
    "auth.register.username": "Username",
    "auth.register.email": "Email (@ulaval.ca)",
    "auth.register.password": "Password",
    "auth.register.submit": "Create account",
    "auth.register.have_account": "Already have an account?",
    "auth.register.login": "Login",
    "auth.verify.title": "Verify your email",
    "auth.verify.subtitle": "Check your inbox and click the verification link to unlock posting and comments.",
    "auth.verify.resend": "Resend verification email",
    "auth.verify.continue": "Continue to feed",
    "auth.verify.back": "Back to login",
    "auth.verify.email_label": "Pending email",
    "auth.forgot.title": "Reset your password",
    "auth.forgot.subtitle": "We will send a reset link if the address exists.",
    "auth.forgot.submit": "Send reset link",
    "auth.forgot.back": "Back to login",
    "auth.reset.title": "Choose a new password",
    "auth.reset.subtitle": "Paste the reset token from the email and set a new password.",
    "auth.reset.token": "Reset token",
    "auth.reset.new_password": "New password",
    "auth.reset.submit": "Reset password",
    "auth.reset.back": "Back to login",
    "common.loading": "Loading...",
    "common.save": "Save",
    "common.cancel": "Cancel",
    "common.close": "Close",
    "common.email": "Email",
    "common.password": "Password",
    "common.success": "Success",
    "error.invalid_ulaval_email": "Email must end with @ulaval.ca",
    "error.password_short": "Password must be at least 8 characters",
    "error.username_required": "Username is required",
    "error.display_name_required": "Display name cannot be empty.",
    "error.network": "Something went wrong. Please try again.",
  },
  fr: {
    "lang.toggle": "EN",
    "app.brand": "PULSE",
    "auth.login.title": "Connexion",
    "auth.login.subtitle": "Connectez-vous pour acceder a votre fil bien-etre du campus",
    "auth.login.email": "Courriel",
    "auth.login.password": "Mot de passe",
    "auth.login.remember": "Se souvenir de moi",
    "auth.login.forgot": "Mot de passe oublie ?",
    "auth.login.submit": "Se connecter",
    "auth.login.no_account": "Pas de compte ?",
    "auth.login.create": "En creer un",
    "auth.register.title": "Creer votre compte",
    "auth.register.username": "Nom d'utilisateur",
    "auth.register.email": "Courriel (@ulaval.ca)",
    "auth.register.password": "Mot de passe",
    "auth.register.submit": "Creer un compte",
    "auth.register.have_account": "Vous avez deja un compte ?",
    "auth.register.login": "Connexion",
    "auth.verify.title": "Verifiez votre courriel",
    "auth.verify.subtitle": "Consultez votre boite de reception puis cliquez sur le lien de verification pour publier et commenter.",
    "auth.verify.resend": "Renvoyer le courriel de verification",
    "auth.verify.continue": "Continuer vers le fil",
    "auth.verify.back": "Retour a la connexion",
    "auth.verify.email_label": "Courriel en attente",
    "auth.forgot.title": "Reinitialisez votre mot de passe",
    "auth.forgot.subtitle": "Nous enverrons un lien de reinitialisation si l'adresse existe.",
    "auth.forgot.submit": "Envoyer le lien",
    "auth.forgot.back": "Retour a la connexion",
    "auth.reset.title": "Choisissez un nouveau mot de passe",
    "auth.reset.subtitle": "Collez le jeton du courriel puis choisissez un nouveau mot de passe.",
    "auth.reset.token": "Jeton de reinitialisation",
    "auth.reset.new_password": "Nouveau mot de passe",
    "auth.reset.submit": "Reinitialiser le mot de passe",
    "auth.reset.back": "Retour a la connexion",
    "common.loading": "Chargement...",
    "common.save": "Enregistrer",
    "common.cancel": "Annuler",
    "common.close": "Fermer",
    "common.email": "Courriel",
    "common.password": "Mot de passe",
    "common.success": "Succes",
    "error.invalid_ulaval_email": "Le courriel doit se terminer par @ulaval.ca",
    "error.password_short": "Le mot de passe doit contenir au moins 8 caracteres",
    "error.username_required": "Le nom d'utilisateur est requis",
    "error.display_name_required": "Le nom affiche ne peut pas etre vide.",
    "error.network": "Une erreur est survenue. Veuillez reessayer.",
  },
};

const STORAGE_KEY = "pulse_lang";

export function getLang() {
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored === "fr" ? "fr" : "en";
}

export function setLang(lang) {
  const nextLang = lang === "fr" ? "fr" : "en";
  localStorage.setItem(STORAGE_KEY, nextLang);
  document.documentElement.lang = nextLang;
  applyTranslations();
  window.dispatchEvent(new CustomEvent("pulse:language-change", { detail: nextLang }));
  return nextLang;
}

export function t(key, vars = {}) {
  const lang = getLang();
  let value = TRANSLATIONS[lang]?.[key] || TRANSLATIONS.en[key] || key;

  Object.entries(vars).forEach(([name, replacement]) => {
    value = value.replaceAll(`{${name}}`, String(replacement));
  });

  return value;
}

function setText(el, value) {
  if (el.dataset.i18nHtml === "true") {
    el.innerHTML = value;
  } else {
    el.textContent = value;
  }
}

export function applyTranslations(root = document) {
  document.documentElement.lang = getLang();

  root.querySelectorAll("[data-i18n]").forEach((el) => {
    setText(el, t(el.dataset.i18n));
  });

  root.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });

  root.querySelectorAll("[data-i18n-title]").forEach((el) => {
    el.title = t(el.dataset.i18nTitle);
  });

  root.querySelectorAll("[data-lang-toggle]").forEach((el) => {
    el.textContent = t("lang.toggle");
  });
}

export function initLanguageControls(root = document) {
  applyTranslations(root);

  root.querySelectorAll("[data-lang-toggle]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const nextLang = getLang() === "en" ? "fr" : "en";
      setLang(nextLang);
    });
  });
}
