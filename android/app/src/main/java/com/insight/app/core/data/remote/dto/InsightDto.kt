package com.insight.app.core.data.remote.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class InsightDto(
    val id: String,
    val category: String,
    val core_thesis: String,
    val logic_chain: List<LogicPointDto>,
    val sources: List<SourceDto>,
    val confidence_score: Float,
    val historical_insight: String?,
    val date_generated: String,
)

@JsonClass(generateAdapter = true)
data class LogicPointDto(
    val premise: String,
    val conclusion: String,
)

@JsonClass(generateAdapter = true)
data class SourceDto(
    val name: String,
    val url: String,
)
