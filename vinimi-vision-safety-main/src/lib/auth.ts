const USER_KEY = "vinimiUser";

export type ManagerSession = {
  id: number;
  name: string;
  email?: string;
  company_id: number;
  created_at?: string;
};

export const getManager = (): ManagerSession | null => {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as ManagerSession) : null;
  } catch {
    return null;
  }
};

export const setManager = (manager: ManagerSession) => {
  try {
    localStorage.setItem(USER_KEY, JSON.stringify(manager));
  } catch {
    /* ignore */
  }
};

export const clearManager = () => {
  try {
    localStorage.removeItem(USER_KEY);
  } catch {
    /* ignore */
  }
};

export const isAuthed = (): boolean => Boolean(getManager());

export const setSession = (manager: ManagerSession) => {
  setManager(manager);
};
