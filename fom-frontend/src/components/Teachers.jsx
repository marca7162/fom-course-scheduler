import { useEffect, useState } from 'react'

const GROUP_ORDER = ['M', 'T', 'W', 'TH', 'F']

function Teachers() {
    const [teachers, setTeachers] = useState({})
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        let mounted = true
        fetch('/api/teacher-schedule')
            .then((res) => {
                if (!res.ok) {
                    throw new Error('Failed to load teacher schedule')
                }
                return res.json()
            })
            .then((data) => {
                const byTeacher = data.reduce((acc, row) => {
                    const name = row.teacherName || row.teacher_name || 'Unknown'
                    acc[name] = acc[name] || []
                    acc[name].push({
                        day: row.day,
                        period: row.period,
                        courseCode: row.courseCode,
                        roomNumber: row.roomNumber,
                    })
                    return acc
                }, {})

                Object.values(byTeacher).forEach((items) => {
                    items.sort((a, b) => {
                        if (a.day === b.day) return Number(a.period) - Number(b.period)
                        return GROUP_ORDER.indexOf(a.day) - GROUP_ORDER.indexOf(b.day)
                    })
                })

                if (mounted) {
                    setTeachers(byTeacher)
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
            fetch('/api/teacher-schedule')
                .then((res) => {
                    if (!res.ok) throw new Error('Failed to load teacher schedule')
                    return res.json()
                })
                .then((data) => {
                    const byTeacher = data.reduce((acc, row) => {
                        const name = row.teacherName || row.teacher_name || 'Unknown'
                        acc[name] = acc[name] || []
                        acc[name].push({
                            day: row.day,
                            period: row.period,
                            courseCode: row.courseCode,
                            roomNumber: row.roomNumber,
                        })
                        return acc
                    }, {})

                    Object.values(byTeacher).forEach((items) => {
                        items.sort((a, b) => {
                            if (a.day === b.day) return Number(a.period) - Number(b.period)
                            return GROUP_ORDER.indexOf(a.day) - GROUP_ORDER.indexOf(b.day)
                        })
                    })

                    if (mounted) {
                        setTeachers(byTeacher)
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
                <div className="alert alert-info">Loading teachers...</div>
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
                    <h2>Teachers</h2>
                    <p className="text-muted">
                        Teacher teaching assignments from the backend schedule.
                    </p>
                </div>
            </div>

            <div className="row gy-4">
                {Object.entries(teachers).map(([name, assignments]) => (
                    <div className="col-md-6" key={name}>
                        <div className="card shadow-sm h-100">
                            <div className="card-header bg-primary text-white">
                                <h5 className="mb-0">{name}</h5>
                            </div>
                            <div className="card-body p-0">
                                <div className="table-responsive">
                                    <table className="table table-sm mb-0">
                                        <thead>
                                            <tr>
                                                <th>Day</th>
                                                <th>Period</th>
                                                <th>Course</th>
                                                <th>Room</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {assignments.map((assignment, index) => (
                                                <tr key={`${name}-${index}`}>
                                                    <td>{assignment.day}</td>
                                                    <td>{assignment.period}</td>
                                                    <td>{assignment.courseCode}</td>
                                                    <td>{assignment.roomNumber}</td>
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

export default Teachers