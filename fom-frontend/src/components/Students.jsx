import { useEffect, useState } from 'react'

function Students() {
    const [students, setStudents] = useState({})
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        let mounted = true
        fetch('/api/student-schedule')
            .then((res) => {
                if (!res.ok) {
                    throw new Error('Failed to load student schedule')
                }
                return res.json()
            })
            .then((data) => {
                const byStudent = data.reduce((acc, row) => {
                    const id = row.studentId || row.student_id || 'Unknown'
                    acc[id] = acc[id] || []
                    acc[id].push({
                        courseCode: row.courseCode,
                        day: row.day,
                        period: row.period,
                        roomNumber: row.roomNumber,
                    })
                    return acc
                }, {})

                Object.values(byStudent).forEach((items) => {
                    const groupedBySlot = items.reduce((acc, item) => {
                        const slotKey = `${item.day}|${item.period}`
                        if (!acc[slotKey]) acc[slotKey] = []
                        acc[slotKey].push(item)
                        return acc
                    }, {})

                    items.forEach((item) => {
                        const slotKey = `${item.day}|${item.period}`
                        item.hasConflict = (groupedBySlot[slotKey]?.length || 0) > 1
                    })

                    items.sort((a, b) => {
                        if (a.day === b.day) return Number(a.period) - Number(b.period)
                        return a.day.localeCompare(b.day)
                    })
                })

                if (mounted) {
                    setStudents(byStudent)
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
            fetch('/api/student-schedule')
                .then((res) => {
                    if (!res.ok) throw new Error('Failed to load student schedule')
                    return res.json()
                })
                .then((data) => {
                    const byStudent = data.reduce((acc, row) => {
                        const id = row.studentId || row.student_id || 'Unknown'
                        acc[id] = acc[id] || []
                        acc[id].push({
                            courseCode: row.courseCode,
                            day: row.day,
                            period: row.period,
                            roomNumber: row.roomNumber,
                        })
                        return acc
                    }, {})

                    Object.values(byStudent).forEach((items) => {
                        const groupedBySlot = items.reduce((acc, item) => {
                            const slotKey = `${item.day}|${item.period}`
                            if (!acc[slotKey]) acc[slotKey] = []
                            acc[slotKey].push(item)
                            return acc
                        }, {})

                        items.forEach((item) => {
                            const slotKey = `${item.day}|${item.period}`
                            item.hasConflict = (groupedBySlot[slotKey]?.length || 0) > 1
                        })

                        items.sort((a, b) => {
                            if (a.day === b.day) return Number(a.period) - Number(b.period)
                            return a.day.localeCompare(b.day)
                        })
                    })

                    if (mounted) {
                        setStudents(byStudent)
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
                <div className="alert alert-info">Loading student schedule...</div>
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
                    <h2>Students</h2>
                    <p className="text-muted">
                        Student enrollment and their scheduled courses from the backend. Conflicts are highlighted in red.
                    </p>
                </div>
            </div>
            <div className="row gy-4">
                {Object.entries(students).map(([studentId, schedule]) => (
                    <div className="col-md-6" key={studentId}>
                        <div className="card shadow-sm h-100">
                            <div className="card-header bg-success text-white">
                                <h5 className="mb-0">Student {studentId}</h5>
                            </div>
                            <div className="card-body p-0">
                                <div className="table-responsive">
                                    <table className="table table-sm mb-0">
                                        <thead>
                                            <tr>
                                                <th>Course</th>
                                                <th>Day</th>
                                                <th>Period</th>
                                                <th>Room</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {schedule.map((item, index) => (
                                                <tr
                                                    key={`${studentId}-${index}`}
                                                    className={item.hasConflict ? 'table-danger' : ''}
                                                >
                                                    <td>
                                                        {item.courseCode}
                                                        {item.hasConflict && (
                                                            <span className="ms-2 badge bg-danger">Conflict</span>
                                                        )}
                                                    </td>
                                                    <td>{item.day}</td>
                                                    <td>{item.period}</td>
                                                    <td>{item.roomNumber}</td>
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

export default Students;