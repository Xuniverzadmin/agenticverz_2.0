// TaskChecklist Component
// M16 Profile Tab - Shows tasks and tests with completion status

import { CheckCircle, Circle, XCircle, ListChecks, FlaskConical } from 'lucide-react';
import { Card, CardBody } from '@/components/common';
import { cn } from '@/lib/utils';

interface Task {
  name: string;
  done: boolean;
}

interface Test {
  name: string;
  passed: boolean | null; // null = not run yet
}

interface TaskChecklistProps {
  tasks: Task[];
  tests: Test[];
  className?: string;
}

export function TaskChecklist({ tasks, tests, className }: TaskChecklistProps) {
  const completedTasks = tasks.filter(t => t.done).length;
  const passedTests = tests.filter(t => t.passed === true).length;
  const failedTests = tests.filter(t => t.passed === false).length;

  return (
    <Card className={className}>
      <CardBody>
        <div className="space-y-4">
          {/* Tasks Section */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <ListChecks className="size-4 text-blue-500" />
                <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Tasks
                </h3>
              </div>
              <span className="text-xs text-gray-500">
                {completedTasks}/{tasks.length} completed
              </span>
            </div>

            {tasks.length > 0 ? (
              <ul className="space-y-2">
                {tasks.map((task, i) => (
                  <li key={i} className="flex items-center gap-2">
                    {task.done ? (
                      <CheckCircle className="size-4 text-green-500 flex-shrink-0" />
                    ) : (
                      <Circle className="size-4 text-gray-300 dark:text-gray-600 flex-shrink-0" />
                    )}
                    <span className={cn(
                      'text-sm',
                      task.done
                        ? 'text-gray-500 line-through'
                        : 'text-gray-900 dark:text-gray-100'
                    )}>
                      {task.name}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400">No tasks defined</p>
            )}
          </div>

          {/* Tests Section */}
          <div className="pt-4 border-t dark:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <FlaskConical className="size-4 text-purple-500" />
                <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Tests
                </h3>
              </div>
              <div className="flex items-center gap-2 text-xs">
                {passedTests > 0 && (
                  <span className="text-green-600">{passedTests} passed</span>
                )}
                {failedTests > 0 && (
                  <span className="text-red-600">{failedTests} failed</span>
                )}
                {passedTests === 0 && failedTests === 0 && tests.length > 0 && (
                  <span className="text-gray-400">Not run</span>
                )}
              </div>
            </div>

            {tests.length > 0 ? (
              <ul className="space-y-2">
                {tests.map((test, i) => (
                  <li key={i} className="flex items-center gap-2">
                    {test.passed === true ? (
                      <CheckCircle className="size-4 text-green-500 flex-shrink-0" />
                    ) : test.passed === false ? (
                      <XCircle className="size-4 text-red-500 flex-shrink-0" />
                    ) : (
                      <Circle className="size-4 text-gray-300 dark:text-gray-600 flex-shrink-0" />
                    )}
                    <span className={cn(
                      'text-sm',
                      test.passed === true && 'text-green-700 dark:text-green-400',
                      test.passed === false && 'text-red-700 dark:text-red-400',
                      test.passed === null && 'text-gray-600 dark:text-gray-400'
                    )}>
                      {test.name}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400">No tests defined</p>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
