"use client";

interface WeekSidebarProps {
    selectedWeek: number;
    onSelectWeek: (week: number) => void;
    weekCounts?: Record<number, number>; // Optional: count of materials per week
}

function classNames(...classes: string[]) {
    return classes.filter(Boolean).join(' ')
}

export default function WeekSidebar({ selectedWeek, onSelectWeek, weekCounts }: WeekSidebarProps) {
    const weeks = Array.from({ length: 14 }, (_, i) => i + 1);

    return (
        <nav aria-label="Sidebar" className="flex flex-1 flex-col overflow-y-auto pb-4">
            <div className="px-4 mb-4">
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                    Course Schedule
                </h3>
            </div>
            <ul role="list" className="space-y-1 px-2">
                {weeks.map((week) => (
                    <li key={week}>
                        <button
                            onClick={() => onSelectWeek(week)}
                            className={classNames(
                                selectedWeek === week
                                    ? 'bg-gray-100 text-indigo-600'
                                    : 'text-gray-700 hover:bg-gray-50 hover:text-indigo-600',
                                'group flex w-full gap-x-3 rounded-md p-2 pl-3 text-sm font-semibold leading-6 text-left transition-colors'
                            )}
                        >
                            Week {week}
                            {weekCounts && weekCounts[week] > 0 && (
                                <span
                                    className="ml-auto w-9 min-w-max whitespace-nowrap rounded-full bg-white px-2.5 py-0.5 text-center text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-200"
                                    aria-hidden="true"
                                >
                                    {weekCounts[week]}
                                </span>
                            )}
                        </button>
                    </li>
                ))}
            </ul>
        </nav>
    )
}
