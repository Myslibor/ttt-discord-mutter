if engine.ActiveGamemode() == "terrortown" then
	AddCSLuaFile()
	require("chttp")

	print("Starting Myslibor TTT Mutter")

	local DISCORD_BOT_URL = "http://127.0.0.1:5003"
	local lastAlive = {}


	--http post
	local function sendToBot(req_type, data)
		data = data or {}
		CHTTP({
			url = DISCORD_BOT_URL .. req_type,
			method = "POST",
			parameters = data,
			success = function(code, body, headers)
				print("Myslibor TTT Mutter: POST success to " ..DISCORD_BOT_URL .. req_type .. ", code: " .. code)
			end,
			failed = function(err)
				print("Myslibor TTT Mutter: POST failed to " .. DISCORD_BOT_URL .. req_type .. ", error: " .. err)
			end
		})
	end

	-- player death
	hook.Add("PlayerDeath", "Myslibor_TTT_MuteOnDeath", function(victim)
		if IsValid(victim) and victim:IsPlayer() then
			print("Myslibor TTT Mutter: player " .. victim:Nick() .. " " .. victim:SteamID64() .. " is dead" )
		sendToBot("/death", {steamid = victim:SteamID64()})
		end
	end)

	--new round 
	hook.Add("TTTBeginRound", "Myslibor_TTT_UnmuteAll", function()
		print("Myslibor TTT Mutter: new round")
		sendToBot("/newround", {})
	end)

	--end round
	hook.Add("TTTEndRound", "Myslibor_TTT_UnmuteAll2", function()
		print("Myslibor TTT Mutter: end round")
		sendToBot("/newround", {})
	end)

	hook.Add("Think", "TTTDetectResurrection", function()
		for _, ply in ipairs(player.GetAll()) do
			if not lastAlive[ply] and ply:Alive() then
				hook.Run("TTTResurrected", ply)
			end
			lastAlive[ply] = ply:Alive()
		end
	end)

	hook.Add("TTTResurrected", "TTTUnMuteRessurected", function(ply)
		sendToBot("/res", {steamid = ply:SteamID64()})
	end)

	concommand.Add("myslibor_printsteamid64", function(ply)
		if IsValid(ply) and ply:IsPlayer() then
			local id = ply:SteamID64()
			print("Myslibor TTT Mutter: " .. ply:Nick() .. " SteamID64 = " .. id)
			ply:ChatPrint("Your SteamID64: " .. id)
		end
	end)


end