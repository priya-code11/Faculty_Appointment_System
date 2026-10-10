<?php
// utils/generate_slots.php

// Ensure argument presence
if ($argc < 2) {
    echo json_encode([
        "status" => "error",
        "message" => "Missing faculty_id argument."
    ]);
    exit(1);
}

$facultyId = $argv[1];
$days = isset($argv[2]) ? (int)$argv[2] : 14;

// Database Configuration (matches your .env credentials)
$dbHost = "localhost";
$dbPort = "5432";
$dbName = "faculty_appointment_db";
$dbUser = "postgres";
$dbPass = "admin@postgre";

try {
    $dsn = "pgsql:host={$dbHost};port={$dbPort};dbname={$dbName};";
    $pdo = new PDO($dsn, $dbUser, $dbPass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
    ]);

    // Check if faculty exists
    $stmtFaculty = $pdo->prepare("SELECT id FROM faculty WHERE id = ?");
    $stmtFaculty->execute([$facultyId]);
    if (!$stmtFaculty->fetch()) {
        echo json_encode(["status" => "error", "message" => "Faculty not found."]);
        exit(1);
    }

    // 1. Fetch master schedule periods sorted by period order
    $stmtPeriods = $pdo->query("SELECT id FROM schedule_periods ORDER BY \"order\" ASC");
    $periodIds = $stmtPeriods->fetchAll(PDO::FETCH_COLUMN);

    $startDate = new DateTime();
    $createdCount = 0;

    for ($offset = 0; $offset < $days; $offset++) {
        $currentDate = (clone $startDate)->modify("+{$offset} days");
        $dateStr = $currentDate->format('Y-m-d');
        // Monday = 0 ... Saturday = 5, Sunday = 6
        $dayOfWeek = (int)$currentDate->format('N') - 1;

        // Skip Sunday
        if ($dayOfWeek > 5) {
            // Remove any slots on Sunday that have zero booking history
            $stmtCleanSunday = $pdo->prepare("
                DELETE FROM appointment_slots s
                WHERE s.faculty_id = ?
                  AND s.date = ?
                  AND NOT EXISTS (
                      SELECT 1 FROM appointments a WHERE a.slot_id = s.id
                  )
            ");
            $stmtCleanSunday->execute([$facultyId, $dateStr]);
            continue;
        }

        // Fetch lecture periods for this weekday
        $stmtLectures = $pdo->prepare("
            SELECT period_id 
            FROM faculty_timetable 
            WHERE faculty_id = ? AND day_of_week = ?
        ");
        $stmtLectures->execute([$facultyId, $dayOfWeek]);
        $lecturePeriodIds = $stmtLectures->fetchAll(PDO::FETCH_COLUMN);

        foreach ($periodIds as $pId) {
            // Check if slot already exists for this faculty, period, and date
            $stmtCheckSlot = $pdo->prepare("
                SELECT id 
                FROM appointment_slots 
                WHERE faculty_id = ? AND period_id = ? AND date = ?
            ");
            $stmtCheckSlot->execute([$facultyId, $pId, $dateStr]);
            $existingSlot = $stmtCheckSlot->fetch();

            // If faculty now has a lecture in this period
            if (in_array($pId, $lecturePeriodIds)) {
                // Delete the slot only if no student appointment ever referenced it
                if ($existingSlot) {
                    $stmtDelete = $pdo->prepare("
                        DELETE FROM appointment_slots s
                        WHERE s.id = ? 
                          AND NOT EXISTS (
                              SELECT 1 FROM appointments a WHERE a.slot_id = s.id
                          )
                    ");
                    $stmtDelete->execute([$existingSlot['id']]);
                }
                continue;
            }

            // If period is free and slot already exists, do not recreate
            if ($existingSlot) {
                continue;
            }

            // Period is free: Create the appointment slot
            $stmtInsert = $pdo->prepare("
                INSERT INTO appointment_slots (id, faculty_id, period_id, date, capacity)
                VALUES (gen_random_uuid(), ?, ?, ?, 5)
            ");
            $stmtInsert->execute([$facultyId, $pId, $dateStr]);
            $createdCount++;
        }
    }

    echo json_encode([
        "status" => "success",
        "faculty_id" => $facultyId,
        "created_count" => $createdCount
    ]);
    exit(0);

} catch (Exception $e) {
    echo json_encode([
        "status" => "error",
        "message" => $e->getMessage()
    ]);
    exit(1);
}