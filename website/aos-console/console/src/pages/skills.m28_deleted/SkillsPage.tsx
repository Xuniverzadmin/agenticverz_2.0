import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Cpu, Search, RefreshCw, Info } from 'lucide-react';
import { Card, CardHeader, CardBody, Spinner, Button, Input } from '@/components/common';
import { getSkills, getSkill, getCapabilities } from '@/api/runtime';
import { formatCredits } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface Skill {
  id?: string;
  skill_id?: string;
  name?: string;
  description?: string;
  cost_estimate_cents?: number;
  rate_limit_remaining?: number;
  available?: boolean;
  parameters?: Record<string, unknown>;
}

export default function SkillsPage() {
  const [search, setSearch] = useState('');
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);

  const { data: skills, isLoading, refetch } = useQuery({
    queryKey: ['skills'],
    queryFn: getSkills,
    refetchInterval: 60000,
  });

  const { data: capabilities } = useQuery({
    queryKey: ['capabilities'],
    queryFn: getCapabilities,
    refetchInterval: 60000,
  });

  const { data: skillDetail, isLoading: loadingDetail } = useQuery({
    queryKey: ['skill-detail', selectedSkill],
    queryFn: () => selectedSkill ? getSkill(selectedSkill) : null,
    enabled: !!selectedSkill,
  });

  // Merge skills from both endpoints
  const skillList: Skill[] = Array.isArray(skills) && skills.length > 0
    ? skills
    : Object.entries(capabilities?.skills || {}).map(([id, s]) => ({
        id,
        skill_id: id,
        ...(s as object)
      }));

  const filteredSkills = skillList.filter((skill) => {
    const name = skill.id || skill.skill_id || skill.name || '';
    return !search || name.toLowerCase().includes(search.toLowerCase());
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            Runtime Skills
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Available capabilities for agent execution
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw size={16} />
        </Button>
      </div>

      {/* Search */}
      <Card>
        <CardBody>
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search skills..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900"
            />
          </div>
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Skills List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader title={`Skills (${filteredSkills.length})`} />
            <CardBody className="p-0">
              {isLoading ? (
                <div className="flex justify-center py-8"><Spinner size="lg" /></div>
              ) : (
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-700/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Skill ID
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Cost
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Rate Limit
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {filteredSkills.map((skill) => {
                      const skillId = skill.id || skill.skill_id || '';
                      return (
                        <tr
                          key={skillId}
                          className={cn(
                            'hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer',
                            selectedSkill === skillId && 'bg-blue-50 dark:bg-blue-900/20'
                          )}
                          onClick={() => setSelectedSkill(skillId)}
                        >
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <Cpu size={16} className="text-gray-400" />
                              <span className="font-mono text-sm">{skillId}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <span className={cn(
                              'px-2 py-0.5 text-xs rounded-full',
                              skill.available !== false
                                ? 'bg-green-100 text-green-700'
                                : 'bg-red-100 text-red-700'
                            )}>
                              {skill.available !== false ? 'Available' : 'Unavailable'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                            {formatCredits(skill.cost_estimate_cents || 0)}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                            {skill.rate_limit_remaining ?? '--'}/min
                          </td>
                          <td className="px-4 py-3">
                            <button
                              className="text-primary-600 hover:text-primary-700"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedSkill(skillId);
                              }}
                            >
                              <Info size={16} />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                    {!filteredSkills.length && (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                          <Cpu className="mx-auto mb-2 text-gray-400" size={32} />
                          No skills found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}
            </CardBody>
          </Card>
        </div>

        {/* Skill Detail */}
        <div>
          <Card>
            <CardHeader title="Skill Details" />
            <CardBody>
              {selectedSkill ? (
                loadingDetail ? (
                  <div className="flex justify-center py-4"><Spinner /></div>
                ) : skillDetail ? (
                  <div className="space-y-4">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase mb-1">Skill ID</p>
                      <p className="font-mono text-sm">{skillDetail.skill_id || skillDetail.id}</p>
                    </div>
                    {skillDetail.description && (
                      <div>
                        <p className="text-xs font-medium text-gray-500 uppercase mb-1">Description</p>
                        <p className="text-sm">{skillDetail.description}</p>
                      </div>
                    )}
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase mb-1">Cost Estimate</p>
                      <p className="text-sm">{formatCredits(skillDetail.cost_estimate_cents || 0)}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase mb-1">Rate Limit</p>
                      <p className="text-sm">{skillDetail.rate_limit_remaining ?? '--'}/min</p>
                    </div>
                    {skillDetail.parameters && (
                      <div>
                        <p className="text-xs font-medium text-gray-500 uppercase mb-1">Parameters</p>
                        <pre className="bg-gray-50 dark:bg-gray-800 p-3 rounded text-xs overflow-auto">
                          {JSON.stringify(skillDetail.parameters, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">Skill details not available</p>
                )
              ) : (
                <p className="text-sm text-gray-500">Select a skill to view details</p>
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
