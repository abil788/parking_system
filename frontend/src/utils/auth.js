export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};

export const getUser = () => {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};

export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
};