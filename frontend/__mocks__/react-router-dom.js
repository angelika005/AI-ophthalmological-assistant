module.exports = {
  BrowserRouter: ({ children }) => children,
  useNavigate: () => jest.fn(),
  useParams: () => ({}),
  useLocation: () => ({ pathname: '/', search: '', hash: '', state: null }),
  useSearchParams: () => [new URLSearchParams(), jest.fn()],
  useRouteMatch: () => ({
    params: {},
    isExact: true,
    path: '/',
    url: '/',
  }),
  Link: ({ children, to }) => children,
  NavLink: ({ children, to }) => children,
  Route: () => null,
  Router: ({ children }) => children,
  Switch: ({ children }) => children,
  Redirect: () => null,
};
