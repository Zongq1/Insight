package com.insight.app.core.domain.model

import com.squareup.moshi.JsonClass

data class Insight(
    val id: String,
    val category: String,
    val coreThesis: String,
    val logicChain: List<LogicPoint>,
    val sources: List<Source>,
    val confidenceScore: Float,
    val historicalInsight: String?,
    val dateGenerated: String,
)

@JsonClass(generateAdapter = true)
data class LogicPoint(
    val premise: String,
    val conclusion: String,
)

@JsonClass(generateAdapter = true)
data class Source(
    val name: String,
    val url: String,
)
