import { useEffect, useState } from 'react'

function Rooms() {
    const [rooms, setRooms] = useState({})
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetch('/api/course-schedule')
            .then((res) => {
                if (!res.ok) {
                    throw new Error('Failed to load course schedule')
                }
                return res.json()
            })
            .then((data) => {
                const byRoom = data.reduce((acc, row) => {
                    const room = row.roomNumber || row.room_number || 'Unknown'
                    acc[room] = acc[room] || []
                    acc[room].push({
                        courseCode: row.courseCode,
                        day: row.day,
                        period: row.period,
                    })
                    return acc
                }, {})

                Object.values(byRoom).forEach((items) => {
                    items.sort((a, b) => {
                        if (a.day === b.day) return Number(a.period) - Number(b.period)
                        return a.day.localeCompare(b.day)
                    })
                })

                setRooms(byRoom)
                setLoading(false)
            })
            .catch((err) => {
                setError(err.message)
                setLoading(false)
            })
    }, [])

    if (loading) {
        return (
            <div className="container mt-4" style={{ paddingTop: '80px' }}>
                <div className="alert alert-info">Loading rooms...</div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="container mt-4" style={{ paddingTop: '80px' }}>
                <div className="alert alert-danger">{error}</div>
            </div>
        )
    }

    return (
        <div className="container mt-4" style={{ paddingTop: '80px' }}>
            <div className="row mb-4">
                <div className="col-12">
                    <h2>Rooms</h2>
                    <p className="text-muted">
                        Room allocation and course assignments from the backend.
                    </p>
                </div>
            </div>

            <div className="row gy-4">
                {Object.entries(rooms).map(([roomName, schedule]) => (
                    <div className="col-md-6" key={roomName}>
                        <div className="card shadow-sm h-100">
                            <div className="card-header bg-secondary text-white">
                                <h5 className="mb-0">{roomName}</h5>
                            </div>
                            <div className="card-body p-0">
                                <div className="table-responsive">
                                    <table className="table table-sm mb-0">
                                        <thead>
                                            <tr>
                                                <th>Course</th>
                                                <th>Day</th>
                                                <th>Period</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {schedule.map((item, index) => (
                                                <tr key={`${roomName}-${index}`}>
                                                    <td>{item.courseCode}</td>
                                                    <td>{item.day}</td>
                                                    <td>{item.period}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default Rooms