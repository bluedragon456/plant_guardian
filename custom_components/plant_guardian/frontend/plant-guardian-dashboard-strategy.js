const CARE_STATES = new Set([
  "dry",
  "low_light",
  "cold",
  "hot",
  "needs_watering",
  "needs_fertilizer",
  "needs_care",
]);

const STATUS_SUFFIX = "_status";

const toTitleCase = (value) =>
  value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());

const slugToName = (slug) => toTitleCase(slug);

const stripStatusSuffix = (value, fallback) => {
  if (!value) {
    return fallback;
  }

  return value.replace(/\s+status$/i, "").trim() || fallback;
};

const buildEntityId = (domain, slug, suffix) => `${domain}.${slug}_${suffix}`;

const plantFromStatus = (hass, stateObj) => {
  const match = stateObj.entity_id.match(/^sensor\.(.+)_status$/);
  if (!match) {
    return undefined;
  }

  const slug = match[1];
  const fallbackName = slugToName(slug);
  const name = stripStatusSuffix(stateObj.attributes.friendly_name, fallbackName);

  const related = {
    status: stateObj.entity_id,
    problem: buildEntityId("binary_sensor", slug, "problem"),
    needsCare: buildEntityId("binary_sensor", slug, "needs_care"),
    daysSinceWatered: buildEntityId("sensor", slug, "days_since_watered"),
    daysSinceFertilized: buildEntityId("sensor", slug, "days_since_fertilized"),
    moisture: buildEntityId("sensor", slug, "moisture"),
    light: buildEntityId("sensor", slug, "light"),
    temperature: buildEntityId("sensor", slug, "temperature"),
    wateredNow: buildEntityId("button", slug, "watered_now"),
    fertilizedNow: buildEntityId("button", slug, "fertilized_now"),
    wateringLogDaysAgo: buildEntityId("number", slug, "watering_log_days_ago"),
    fertilizingLogDaysAgo: buildEntityId("number", slug, "fertilizing_log_days_ago"),
    wateredSelectedDay: buildEntityId("button", slug, "watered_selected_day"),
    fertilizedSelectedDay: buildEntityId("button", slug, "fertilized_selected_day"),
  };

  return {
    slug,
    name,
    path: slug,
    state: stateObj,
    entities: related,
    hasMoisture: Boolean(hass.states[related.moisture]),
    hasLight: Boolean(hass.states[related.light]),
    hasTemperature: Boolean(hass.states[related.temperature]),
    hasProblem: Boolean(hass.states[related.problem]),
    hasNeedsCare: Boolean(hass.states[related.needsCare]),
    hasWaterButton: Boolean(hass.states[related.wateredNow]),
    hasFertilizerButton: Boolean(hass.states[related.fertilizedNow]),
    hasWaterBackfill: Boolean(hass.states[related.wateringLogDaysAgo] && hass.states[related.wateredSelectedDay]),
    hasFertilizerBackfill: Boolean(
      hass.states[related.fertilizingLogDaysAgo] && hass.states[related.fertilizedSelectedDay]
    ),
  };
};

const discoverPlants = (hass) =>
  Object.values(hass.states)
    .filter(
      (stateObj) =>
        stateObj.entity_id.startsWith("sensor.") &&
        stateObj.entity_id.endsWith(STATUS_SUFFIX) &&
        stateObj.attributes.days_since_watered !== undefined &&
        stateObj.attributes.days_since_fertilized !== undefined &&
        stateObj.attributes.needs_care !== undefined
    )
    .map((stateObj) => plantFromStatus(hass, stateObj))
    .filter(Boolean)
    .sort((left, right) => left.name.localeCompare(right.name));

const buildButtonPressCard = (entityId, name, icon) => ({
  type: "button",
  name,
  icon,
  tap_action: {
    action: "call-service",
    service: "button.press",
    target: { entity_id: entityId },
  },
});

const buildMetricTile = (entityId, name, color) => ({
  type: "tile",
  entity: entityId,
  name,
  color,
});

const buildEntityTile = (entityId, name, icon) => ({
  type: "tile",
  entity: entityId,
  name,
  icon,
});

const buildGaugeCard = (entityId, name, min, max, low, good) => ({
  type: "gauge",
  entity: entityId,
  name,
  min,
  max,
  needle: true,
  severity: {
    red: min,
    yellow: Math.min(good, Math.max(low, min)),
    green: Math.max(good, low),
  },
});

const buildOverviewView = (plants) => {
  const carePlants = plants.filter((plant) => CARE_STATES.has(plant.state.state));
  const healthyPlants = plants.length - carePlants.length;
  const buttonCards = plants
    .filter((plant) => plant.hasWaterButton)
    .slice(0, 6)
    .map((plant) =>
      buildButtonPressCard(plant.entities.wateredNow, `Water ${plant.name}`, "mdi:watering-can")
    );

  return {
    title: "Snapshot",
    path: "snapshot",
    icon: "mdi:view-dashboard-outline",
    type: "sections",
    max_columns: 4,
    sections: [
      {
        type: "grid",
        cards: [
          {
            type: "heading",
            heading: "Plant Guardian",
            heading_style: "title",
            icon: "mdi:sprout-outline",
          },
          {
            type: "markdown",
            content: `Tracking ${plants.length} plant(s): ${healthyPlants} stable and ${carePlants.length} needing care.`,
          },
        ],
      },
      {
        type: "grid",
        cards: [
          {
            type: "heading",
            heading: "Attention Queue",
            icon: "mdi:alert-decagram-outline",
          },
          carePlants.length
            ? {
                type: "entity-filter",
                show_empty: false,
                state_filter: Array.from(CARE_STATES),
                entities: plants.map((plant) => ({
                  entity: plant.entities.status,
                  name: plant.name,
                })),
                card: {
                  type: "entities",
                  title: "Plants needing care now",
                },
              }
            : {
                type: "markdown",
                content: "No plants currently need care.",
              },
        ],
      },
      {
        type: "grid",
        cards: [
          {
            type: "heading",
            heading: "Portfolio Tiles",
            icon: "mdi:view-grid-plus-outline",
          },
          {
            type: "grid",
            columns: Math.min(3, Math.max(plants.length, 1)),
            square: false,
            cards: plants.flatMap((plant) => {
              const cards = [
                {
                  type: "tile",
                  entity: plant.entities.status,
                  name: plant.name,
                  vertical: true,
                },
              ];

              if (plant.hasNeedsCare) {
                cards.push(buildMetricTile(plant.entities.needsCare, `${plant.name} care`, "amber"));
              }

              return cards;
            }),
          },
        ],
      },
      {
        type: "grid",
        cards: [
          {
            type: "heading",
            heading: "Care Cadence",
            icon: "mdi:calendar-heart",
          },
          {
            type: "entities",
            title: "Watering and feeding age",
            show_header_toggle: false,
            entities: plants.flatMap((plant) => [
              { entity: plant.entities.daysSinceWatered, name: `${plant.name} watered` },
              { entity: plant.entities.daysSinceFertilized, name: `${plant.name} fertilized` },
            ]),
          },
        ],
      },
      {
        type: "grid",
        cards: [
          {
            type: "heading",
            heading: "Quick Logging",
            icon: "mdi:gesture-tap-button",
          },
          buttonCards.length
            ? {
                type: "grid",
                columns: Math.min(3, Math.max(buttonCards.length, 1)),
                square: false,
                cards: buttonCards,
              }
            : {
                type: "markdown",
                content: "No logging buttons were discovered yet.",
              },
        ],
      },
      {
        type: "grid",
        cards: [
          {
            type: "heading",
            heading: "Weekly Status History",
            icon: "mdi:chart-timeline-variant",
          },
          {
            type: "history-graph",
            title: "Status changes across the collection",
            hours_to_show: 168,
            entities: plants.slice(0, 8).map((plant) => plant.entities.status),
          },
        ],
      },
    ],
  };
};

const buildDetailMetricsSection = (plant) => {
  const attrs = plant.state.attributes;
  const cards = [buildMetricTile(plant.entities.status, "Overall Status", "green")];

  if (plant.hasProblem) {
    cards.push(buildMetricTile(plant.entities.problem, "Problem Active", "red"));
  }

  if (plant.hasNeedsCare) {
    cards.push(buildMetricTile(plant.entities.needsCare, "Needs Care", "amber"));
  }

  cards.push(buildMetricTile(plant.entities.daysSinceWatered, "Days Since Watered", "blue"));
  cards.push(buildMetricTile(plant.entities.daysSinceFertilized, "Days Since Fertilized", "green"));

  if (plant.hasMoisture) {
    const moistureMin = Number(attrs.moisture_min ?? 25);
    cards.push(
      buildGaugeCard(
        plant.entities.moisture,
        "Moisture",
        0,
        100,
        moistureMin,
        Math.min(100, moistureMin + 15)
      )
    );
  }

  if (plant.hasLight) {
    const lightMin = Number(attrs.light_min ?? 300);
    const currentLight = Number(attrs.light ?? 0);
    const max = Math.max(1000, lightMin * 2, currentLight * 1.4);
    cards.push(buildGaugeCard(plant.entities.light, "Light", 0, max, lightMin, lightMin * 1.5));
  }

  if (plant.hasTemperature) {
    cards.push(buildMetricTile(plant.entities.temperature, "Temperature", "orange"));
  }

  return {
    type: "grid",
    cards: [
      {
        type: "heading",
        heading: "Live Status",
        icon: "mdi:heart-pulse",
      },
      {
        type: "grid",
        columns: 2,
        square: false,
        cards,
      },
    ],
  };
};

const buildDetailView = (plant) => {
  const detailRows = [
    { entity: plant.entities.status, name: "Status" },
    { entity: plant.entities.daysSinceWatered, name: "Days since watered" },
    { entity: plant.entities.daysSinceFertilized, name: "Days since fertilized" },
    { type: "attribute", entity: plant.entities.status, attribute: "species", name: "Species" },
    { type: "attribute", entity: plant.entities.status, attribute: "last_watered", name: "Last watered" },
    { type: "attribute", entity: plant.entities.status, attribute: "last_fertilized", name: "Last fertilized" },
    { type: "attribute", entity: plant.entities.status, attribute: "care_summary", name: "Care summary" },
    { type: "attribute", entity: plant.entities.status, attribute: "care_source", name: "Care source" },
    { type: "attribute", entity: plant.entities.status, attribute: "watering_interval_days", name: "Watering interval" },
    { type: "attribute", entity: plant.entities.status, attribute: "fertilizing_interval_days", name: "Fertilizing interval" },
    { type: "attribute", entity: plant.entities.status, attribute: "watering_log_days_ago", name: "Water log days ago" },
    {
      type: "attribute",
      entity: plant.entities.status,
      attribute: "fertilizing_log_days_ago",
      name: "Fertilizer log days ago",
    },
  ];

  if (plant.hasMoisture) {
    detailRows.push({
      type: "attribute",
      entity: plant.entities.status,
      attribute: "moisture_min",
      name: "Minimum moisture",
    });
  }

  if (plant.hasLight) {
    detailRows.push({
      type: "attribute",
      entity: plant.entities.status,
      attribute: "light_min",
      name: "Minimum light",
    });
  }

  if (plant.hasTemperature) {
    detailRows.push(
      {
        type: "attribute",
        entity: plant.entities.status,
        attribute: "temp_min",
        name: "Minimum temperature",
      },
      {
        type: "attribute",
        entity: plant.entities.status,
        attribute: "temp_max",
        name: "Maximum temperature",
      }
    );
  }

  const actionCards = [];
  if (plant.hasWaterButton) {
    actionCards.push(buildButtonPressCard(plant.entities.wateredNow, "Mark watered", "mdi:watering-can"));
  }
  if (plant.hasFertilizerButton) {
    actionCards.push(
      buildButtonPressCard(plant.entities.fertilizedNow, "Mark fertilized", "mdi:sprout-outline")
    );
  }

  const historyEntities = [plant.entities.status];
  if (plant.hasMoisture) {
    historyEntities.push(plant.entities.moisture);
  }
  if (plant.hasLight) {
    historyEntities.push(plant.entities.light);
  }
  if (plant.hasTemperature) {
    historyEntities.push(plant.entities.temperature);
  }

  return {
    title: plant.name,
    path: plant.path,
    icon: "mdi:leaf",
    type: "sections",
    max_columns: 4,
    sections: [
      {
        type: "grid",
        cards: [
          {
            type: "heading",
            heading: plant.name,
            heading_style: "title",
            icon: "mdi:leaf-circle-outline",
          },
          {
            type: "picture-entity",
            entity: plant.entities.status,
            name: plant.name,
            show_name: true,
            show_state: true,
          },
        ],
      },
      buildDetailMetricsSection(plant),
      {
        type: "grid",
        cards: [
          {
            type: "heading",
            heading: "Care Actions",
            icon: "mdi:gesture-tap-button",
          },
          ...(plant.hasWaterBackfill || plant.hasFertilizerBackfill
            ? [
                {
                  type: "grid",
                  columns: 2,
                  square: false,
                  cards: [
                    ...(plant.hasWaterBackfill
                      ? [
                          buildEntityTile(
                            plant.entities.wateringLogDaysAgo,
                            "Water log days ago",
                            "mdi:calendar-edit"
                          ),
                          buildButtonPressCard(
                            plant.entities.wateredSelectedDay,
                            "Log watering from selected day",
                            "mdi:calendar-water"
                          ),
                        ]
                      : []),
                    ...(plant.hasFertilizerBackfill
                      ? [
                          buildEntityTile(
                            plant.entities.fertilizingLogDaysAgo,
                            "Fertilizer log days ago",
                            "mdi:calendar-edit"
                          ),
                          buildButtonPressCard(
                            plant.entities.fertilizedSelectedDay,
                            "Log fertilizing from selected day",
                            "mdi:calendar-arrow-left"
                          ),
                        ]
                      : []),
                  ],
                },
              ]
            : []),
          actionCards.length
            ? {
                type: "horizontal-stack",
                cards: actionCards,
              }
            : {
                type: "markdown",
                content: "No Plant Guardian action buttons were discovered for this plant.",
              },
        ],
      },
      {
        type: "grid",
        cards: [
          {
            type: "heading",
            heading: "Care Details",
            icon: "mdi:text-box-search-outline",
          },
          {
            type: "entities",
            title: "Plant profile",
            show_header_toggle: false,
            entities: detailRows,
          },
        ],
      },
      {
        type: "grid",
        cards: [
          {
            type: "heading",
            heading: "Recent Trends",
            icon: "mdi:chart-line",
          },
          {
            type: "history-graph",
            title: `Past 7 days for ${plant.name}`,
            hours_to_show: 168,
            entities: historyEntities,
          },
        ],
      },
    ],
  };
};

const buildEmptyDashboard = () => ({
  title: "Plant Guardian",
  views: [
    {
      title: "Plant Guardian",
      path: "plant-guardian",
      icon: "mdi:sprout-outline",
      cards: [
        {
          type: "markdown",
          content:
            "No Plant Guardian plants were discovered yet. Add one or more plants in Settings > Devices & services, then reload this dashboard.",
        },
      ],
    },
  ],
});

class PlantGuardianAutoStrategy extends HTMLElement {
  static async generateDashboard(info) {
    const plants = discoverPlants(info.hass);

    if (!plants.length) {
      return buildEmptyDashboard();
    }

    return {
      title: "Plant Guardian",
      views: [buildOverviewView(plants), ...plants.map((plant) => buildDetailView(plant))],
    };
  }
}

if (!customElements.get("ll-strategy-plant-guardian-auto")) {
  customElements.define("ll-strategy-plant-guardian-auto", PlantGuardianAutoStrategy);
}
