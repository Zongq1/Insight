package com.insight.app.core.domain.model

data class Topic(
    val id: String,
    val name: String,
    val keywords: List<String>,
    val lastFetchedAt: String?,
)
