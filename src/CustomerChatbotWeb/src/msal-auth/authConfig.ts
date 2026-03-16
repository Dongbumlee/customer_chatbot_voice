import { Configuration, LogLevel } from "@azure/msal-browser";

/**
 * MSAL configuration for Microsoft Entra ID authentication.
 * Replace placeholder values with your Azure AD app registration details.
 */
export const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_AZURE_CLIENT_ID ?? "",
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_AZURE_TENANT_ID ?? "common"}`,
    redirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      logLevel: LogLevel.Warning,
    },
  },
};

/** Scopes requested when acquiring tokens for the backend API. */
export const apiScopes = [
  `api://${import.meta.env.VITE_AZURE_CLIENT_ID ?? ""}/access_as_user`,
];
