package com.insight.app.core.data.local.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.insight.app.core.data.local.entity.InsightEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface InsightDao {

    @Query("SELECT * FROM insights ORDER BY createdAt DESC")
    fun getAllInsights(): Flow<List<InsightEntity>>

    @Query("SELECT * FROM insights WHERE category = :category ORDER BY createdAt DESC")
    fun getInsightsByCategory(category: String): Flow<List<InsightEntity>>

    @Query("SELECT * FROM insights WHERE id = :id")
    suspend fun getInsightById(id: String): InsightEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertInsight(insight: InsightEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertInsights(insights: List<InsightEntity>)

    @Update
    suspend fun updateInsight(insight: InsightEntity)

    @Delete
    suspend fun deleteInsight(insight: InsightEntity)

    @Query("DELETE FROM insights")
    suspend fun deleteAllInsights()

    @Query("SELECT COUNT(*) FROM insights")
    suspend fun count(): Int
}
