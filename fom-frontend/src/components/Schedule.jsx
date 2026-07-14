function Schedule() {
    return (
        <div>
            <div className="page-header">
                <h1 className="display-6 fw-bold">FOM Schedule Overview</h1>
                <p className="text-muted">
                    A simple front-end shell for the generated course schedule.
                </p>
            </div>

            <div className="row g-4">
                <div className="col-md-4">
                    <div className="card summary-card h-100">
                        <div className="card-body">
                            <h5 className="card-title">Today</h5>
                            <p className="card-text text-muted">Review the timetable for the current teaching day.</p>
                            <span className="badge badge-soft rounded-pill">Live</span>
                        </div>
                    </div>
                </div>
                <div className="col-md-4">
                    <div className="card summary-card h-100">
                        <div className="card-body">
                            <h5 className="card-title">Rooms</h5>
                            <p className="card-text text-muted">Track room allocation and availability.</p>
                        </div>
                    </div>
                </div>
                <div className="col-md-4">
                    <div className="card summary-card h-100">
                        <div className="card-body">
                            <h5 className="card-title">Students</h5>
                            <p className="card-text text-muted">Keep course and enrollment details visible.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Schedule
