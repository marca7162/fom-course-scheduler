import { NavLink } from 'react-router-dom'

function Nav() {
    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-light shadow-sm">
            <div className="container">
                <NavLink className="navbar-brand fw-bold" to="/">
                    FOM Schedule
                </NavLink>
                <button
                    className="navbar-toggler"
                    type="button"
                    data-bs-toggle="collapse"
                    data-bs-target="#navbarSupportedContent"
                    aria-controls="navbarSupportedContent"
                    aria-expanded="false"
                    aria-label="Toggle navigation"
                >
                    <span className="navbar-toggler-icon"></span>
                </button>

              <div className="collapse navbar-collapse" id="navbarSupportedContent">
                  <ul className="navbar-nav ms-auto mb-2 mb-lg-0">
                      <li className="nav-item">
                          <NavLink
                              to="/"
                              className={({ isActive }) =>
                                  isActive ? 'nav-link active' : 'nav-link'
                              }
                          >
                              Home
                          </NavLink>
                      </li>
                      <li className="nav-item">
                          <NavLink
                              to="/teachers"
                              className={({ isActive }) =>
                                  isActive ? 'nav-link active' : 'nav-link'
                              }
                          >
                              Teachers
                          </NavLink>
                      </li>
                      <li className="nav-item">
                          <NavLink
                              to="/students"
                              className={({ isActive }) =>
                                  isActive ? 'nav-link active' : 'nav-link'
                              }
                          >
                              Students
                          </NavLink>
                      </li>
                      <li className="nav-item">
                          <NavLink
                              to="/rooms"
                              className={({ isActive }) =>
                                  isActive ? 'nav-link active' : 'nav-link'
                              }
                          >
                              Rooms
                          </NavLink>
                      </li>
                  </ul>
              </div>
          </div>
      </nav>
  )
}

export default Nav