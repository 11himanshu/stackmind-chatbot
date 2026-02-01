import { Navigate } from 'react-router-dom'

/*
  RequireAuth
  -----------
  Route guard component.
  - Allows access only if token + user exist
  - Redirects to /login otherwise
*/

const RequireAuth = ({ children }) => {
  const token = localStorage.getItem('token')
  const user = localStorage.getItem('user')

  if (!token || !user) {
    return <Navigate to="/login" replace />
  }

  return children
}

export default RequireAuth