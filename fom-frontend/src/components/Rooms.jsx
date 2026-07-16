import { useEffect, useState } from 'react'

const DAY_ORDER = ['M', 'T', 'W', 'TH', 'F']

function formatDayGroup(days) {
    const uniqueDays = [...new Set(days)]
    if (uniqueDays.length === 2 && uniqueDays.includes('M') && uniqueDays.includes('W')) return 'MW'
    if (uniqueDays.length === 2 && uniqueDays.includes('T') && uniqueDays.includes('TH')) return 'TTH'
    return uniqueDays.sort((a, b) => DAY_ORDER.indexOf(a) - DAY_ORDER.indexOf(b)).join('/')
}

function buildRoomSchedules(data) {
    const byRoom = data.reduce((acc, row) => {
        const room = row.roomNumber || row.room_number || 'Unknown'
        acc[room] = acc[room] || []
        const key = `${row.courseCode}|${row.period}`
        let meeting = acc[room].find((item) => item.key === key)
        if (!meeting) {
            meeting = { key, days: [], courseCode: row.courseCode, period: row.period }
            acc[room].push(meeting)
        }
        meeting.days.push(row.day)
        return acc
    }, {})

    Object.values(byRoom).forEach((items) => {
        items.forEach((item) => {
            item.day = formatDayGroup(item.days)
            delete item.days
            delete item.key
        })
        items.sort((a, b) => {
            const dayDifference = DAY_ORDER.indexOf(a.day[0]) - DAY_ORDER.indexOf(b.day[0])
            return dayDifference || Number(a.period) - Number(b.period)
        })
    })
    return byRoom
}

function Rooms() {
    const [rooms, setRooms] = useState({})
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        let mounted = true;
        fetch('/api/course-schedule')
            .then((res) => {
                if (!res.ok) {
                    throw new Error('Failed to load course schedule')
                }
                return res.json()
            })
            .then((data) => {
                const byRoom = buildRoomSchedules(data)

                if (mounted) {
                    setRooms(byRoom)
                    setLoading(false)
                }
            })
            .catch((err) => {
                if (mounted) {
                    setError(err.message)
                    setLoading(false)
                }
            })
        const onChange = () => {
            // re-fetch when schedule changes elsewhere
            fetch('/api/course-schedule')
                .then((res) => {
                    if (!res.ok) throw new Error('Failed to load course schedule')
                    return res.json()
                })
                .then((data) => {
                    const byRoom = buildRoomSchedules(data)

                    if (mounted) {
                        setRooms(byRoom)
                        setLoading(false)
                    }
                })
                .catch((err) => {
                    if (mounted) {
                        setError(err.message)
                        setLoading(false)
                    }
                })
        }

        window.addEventListener('scheduleChanged', onChange)

        return () => {
            mounted = false
            window.removeEventListener('scheduleChanged', onChange)
        }
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
