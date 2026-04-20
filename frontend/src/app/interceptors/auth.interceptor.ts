import { HttpInterceptorFn } from '@angular/common/http';

const PUBLIC_PATHS = [
  '/auth/login/',
  '/auth/register/',
  '/options/',
  '/products/',
  '/match/',
  '/analyze-face/',
  '/check-ingredients/'
];

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const isPublicRequest = PUBLIC_PATHS.some((path) => req.url.includes(path));
  if (isPublicRequest) {
    return next(req);
  }

  const token = localStorage.getItem('token');

  if (token) {
    const cloned = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
    return next(cloned);
  }

  return next(req);
};
