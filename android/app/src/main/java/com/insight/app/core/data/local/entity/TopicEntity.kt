package com.insight.app.core.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "topics")
data class TopicEntity(
    @PrimaryKey
    val id: String,
    val name: String,
    val keywordsJson: String,
    val lastFetchedAt: Long? = null,
    val createdAt: Long = System.currentTimeMillis(),
)
