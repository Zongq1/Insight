package com.insight.app.feature.insight

import com.insight.app.core.domain.model.Insight

data class InsightState(
    val insights: List<Insight> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val selectedCategory: String? = null,
    val deletedIds: Set<String> = emptySet(),
)
