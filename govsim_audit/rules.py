from __future__ import annotations
# Faithful transcription of the code displayed in arXiv:2609.22600v2,
# Appendix I, PDF pages 43–45. Formatting normalized from the printed PDF.
def survival_population_limit(world):
    """
    Emergency measure: when stock is critically low (< 60% of capacity),
    adjusts population to what the lake can sustainably support.
    Removes agents with fewest rounds_active (newest first) to protect
    the established community. Only activates in true crisis conditions.
    """
    # Only activate in crisis
    if world.stock < 0.6 * world.capacity:
        # Calculate maximum sustainable population
        # Based on: capacity * 50% regeneration / poverty_line
        sustainable_catch = world.capacity * 0.5
        max_sustainable = max(1, int(sustainable_catch / world.poverty_line))
        active_agents = [a for a in world.agents if a.active]
        if len(active_agents) > max_sustainable:
            # Sort by rounds_active - remove newest members first
            active_agents.sort(key=lambda a: a.rounds_active)
            excess = len(active_agents) - max_sustainable
            for i in range(excess):
                active_agents[i].active = False
    return world

def emergency_cull_rule(world) -> world:
    survivors = int(world.stock // world.poverty_line)
    if survivors == 0:
        survivors = 1  # Ensure at least 1
    target_active = min(survivors, len(world.agents))
    # Mark excess as inactive
    for i, agent in enumerate(world.agents):
        if i >= target_active:
            agent.active = False
    return world

def right_size_fleet(world) -> world:
    """
    Reduces active agents to sustainable levels given available resources.
    """
    active_agents = sorted([a for a in world.agents if a.active],
                           key=lambda a: a.name)
    if len(active_agents) == 0:
        return world
    available_resources = world.stock + world.treasury
    max_sustainable_agents = max(1, int(available_resources / world.poverty_line))
    for i, agent in enumerate(active_agents):
        if i >= max_sustainable_agents:
            agent.active = False
        else:
            agent.catch_cap = world.poverty_line
    return world

# Appendix D.5, PDF pp. 25–26. The paper omits some original comments.
def emergency_population_cap(world):
    """
    When stock falls critically low, temporarily caps active agents to what
    the sustainable stock can support, using fair lottery among those who
    haven't been recently deactivated.
    """
    sustainable_threshold = world.capacity / 2  # 28 for capacity 56
    if world.stock < sustainable_threshold:
        available_for_catch = max(0, world.stock - sustainable_threshold * 0.5)
        sustainable_agents = max(1, int(available_for_catch / world.poverty_line))
        active_agents = [a for a in world.agents if a.active]
        if len(active_agents) > sustainable_agents:
            # Sort by rounds_active (fewer rounds = higher priority to stay)
            active_agents.sort(key=lambda a: a.rounds_active)
            # Keep the first sustainable_agents, deactivate the rest
            for i, agent in enumerate(active_agents):
                if i >= sustainable_agents:
                    agent.active = False
    return world
