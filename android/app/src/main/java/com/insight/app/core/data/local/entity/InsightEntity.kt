package com.insight.app.core.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "insights")
data class InsightEntity(
    @PrimaryKey
    val id: String,
    val category: String,
    val coreThesis: String,
    val logicChainJson: String,
    val sourcesJson: String,
    val confidenceScore: Float,
    val historicalInsight: String?,
    val createdAt: Long = System.currentTimeMillis(),
)
