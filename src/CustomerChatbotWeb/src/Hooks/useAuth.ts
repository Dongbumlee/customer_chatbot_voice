import { useMsal } from "@azure/msal-react";
import { apiScopes } from "../msal-auth/authConfig";

/**
 * Authentication hook — wraps MSAL login/logout and token acquisition.
 */
export function useAuth() {
    const { instance, accounts } = useMsal();

    const login = async () => {
        await instance.loginPopup({ scopes: apiScopes });
    };

    const logout = async () => {
        await instance.logoutPopup();
    };

    const getAccessToken = async (): Promise<string> => {
        const account = accounts[0];
        if (!account) throw new Error("No authenticated account");
        const response = await instance.acquireTokenSilent({
            scopes: apiScopes,
            account,
        });
        return response.accessToken;
    };

    return { login, logout, getAccessToken, account: accounts[0] };
}
