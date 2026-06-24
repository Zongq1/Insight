package com.insight.app.core.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.insight.app.core.data.local.converter.Converters
import com.insight.app.core.data.local.dao.InsightDao
import com.insight.app.core.data.local.dao.TopicDao
import com.insight.app.core.data.local.entity.InsightEntity
import com.insight.app.core.data.local.entity.TopicEntity

@Database(
    entities = [InsightEntity::class, TopicEntity::class],
    version = 1,
    exportSchema = true,
)
@TypeConverters(Converters::class)
abstract class InsightDatabase : RoomDatabase() {
    abstract fun insightDao(): InsightDao
    abstract fun topicDao(): TopicDao
}
