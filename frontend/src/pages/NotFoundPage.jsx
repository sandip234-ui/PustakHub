/**
 * NotFoundPage — 404 fallback page.
 */

import { Link } from "react-router-dom";

function NotFoundPage() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-700">404</h1>
        <p className="mt-4 text-xl text-gray-400">Page not found</p>
        <Link
          to="/"
          className="mt-6 inline-block text-indigo-400 hover:text-indigo-300 underline"
        >
          Go to Home
        </Link>
      </div>
    </div>
  );
}

export default NotFoundPage;
